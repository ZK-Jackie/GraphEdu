"""章节管理服务模块

该模块提供章节信息的管理功能。

职责：
1. 接收 DTO，转换为 ORM 对象。
2. 处理业务逻辑。
3. 将 ORM 对象转换为 VO 返回。
"""

from datetime import datetime
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.exceptions.services.education.chapter import (
    ChapterCreateFailedException,
    ChapterIdListEmptyException,
    ChapterLoopException,
    ChapterNameAlreadyExistsException,
    ChapterNoPermissionException,
    ChapterNotFoundException,
    ChapterUpdateFailedException,
)
from graphedu.common.exceptions.services.education.course import CourseNotFoundException
from graphedu.common.models import SystemConstants
from graphedu.common.models.bo import CurrentUser
from graphedu.common.models.dto.educationv2.chapter import ChapterCreateDTO, ChapterQueryDTO, ChapterUpdateDTO
from graphedu.common.models.orm.education import EduChapter
from graphedu.common.models.vo.base import BatchDeleteResponse, DeleteResultItem, PageResponse
from graphedu.common.models.vo.educationv2.chapter import (
    ChapterDescriptionResultVO,
    ChapterDetailVO,
    ChapterListVO,
    ChapterTreeBriefVO,
    ChapterTreeVO,
)
from graphedu.common.models.vo.educationv2.chapter_resource import (
    ChapterResourceBatchDeleteResultVO,
    ChapterResourceDetailVO,
    ChapterResourceListVO,
)
from graphedu.common.models.vo.educationv2.knowledge_graph import (
    ChapterKnowledgePointLinkResultVO,
    KnowledgeNodeChapterDetailVO,
)
from graphedu.common.resource import AsyncPostgresqlClient
from graphedu.mapper.education.chapter import ChapterMapper
from graphedu.mapper.education.chapter_knowledge_point import ChapterKnowledgePointMapper
from graphedu.mapper.education.course import CourseMapper
from graphedu.services.education.chapter_resource import ChapterResourceService
from graphedu.services.external.graphrag import GraphRAGService

logger = logging.getLogger(__name__)


# ============================================================================
# ORM → VO 转换函数
# ============================================================================


def _convert_chapter_orm_to_list_vo(chapter_orm: EduChapter) -> ChapterListVO:
    """将章节 ORM 对象转换为 ChapterListVO。

    Args:
        chapter_orm: 章节 ORM 对象。

    Returns:
        ChapterListVO: 章节列表项 VO。
    """
    return ChapterListVO(
        chapter_id=chapter_orm.chapter_id,
        course_id=chapter_orm.course_id,
        parent_id=chapter_orm.parent_id,
        chapter_name=chapter_orm.chapter_name,
        chapter_no=chapter_orm.chapter_no,
        description=chapter_orm.description,
        status=chapter_orm.status,
        create_time=chapter_orm.create_time,
    )


def _convert_chapter_orm_to_detail_vo(chapter_orm: EduChapter) -> ChapterDetailVO:
    """将章节 ORM 对象转换为 ChapterDetailVO。

    Args:
        chapter_orm: 章节 ORM 对象。

    Returns:
        ChapterDetailVO: 章节详细信息 VO。
    """
    return ChapterDetailVO(
        chapter_id=chapter_orm.chapter_id,
        course_id=chapter_orm.course_id,
        parent_id=chapter_orm.parent_id,
        chapter_name=chapter_orm.chapter_name,
        chapter_no=chapter_orm.chapter_no,
        description=chapter_orm.description,
        status=chapter_orm.status,
        create_by=chapter_orm.create_by,
        create_time=chapter_orm.create_time,
        update_by=chapter_orm.update_by,
        update_time=chapter_orm.update_time,
    )


def _convert_chapter_orm_to_tree_vo(
    chapter_orm: EduChapter, content_count: int = 0, has_children: bool | None = None
) -> ChapterTreeVO:
    """将章节 ORM 对象转换为 ChapterTreeVO。

    Args:
        chapter_orm: 章节 ORM 对象。
        content_count: 资料数量。
        has_children: 是否有子章节（用于懒加载模式）。

    Returns:
        ChapterTreeVO: 章节树形结构 VO。
    """
    return ChapterTreeVO(
        chapter_id=chapter_orm.chapter_id,
        course_id=chapter_orm.course_id,
        parent_id=chapter_orm.parent_id,
        chapter_name=chapter_orm.chapter_name,
        chapter_no=chapter_orm.chapter_no,
        description=chapter_orm.description,
        status=chapter_orm.status,
        content_count=content_count,
        has_children=has_children,
        children=None,
    )


# ============================================================================
# 内部校验函数
# ============================================================================


async def _check_chapter_name_exists(
    course_id: int, chapter_name: str, parent_id: int, query_db: AsyncSession, exclude_chapter_id: int = None
) -> bool:
    """校验章节名称是否存在于同一课程下。

    Args:
        course_id: 课程 ID。
        chapter_name: 章节名称。
        parent_id: 父章节 ID。
        query_db: 数据库会话。
        exclude_chapter_id: 排除的章节 ID（用于编辑时校验）。

    Returns:
        bool: 章节名称是否存在。
    """
    from sqlalchemy import and_, select

    conditions = [
        EduChapter.course_id == course_id,
        EduChapter.chapter_name == chapter_name,
        EduChapter.parent_id == parent_id,
        EduChapter.status != SystemConstants.Status.DELETED,
    ]

    if exclude_chapter_id:
        conditions.append(EduChapter.chapter_id != exclude_chapter_id)

    stmt = select(EduChapter).where(and_(*conditions))
    existing_chapter = (await query_db.execute(stmt)).scalars().first()
    return existing_chapter is not None


async def _check_chapter_loop(chapter_id: int, new_parent_id: int, query_db: AsyncSession) -> None:
    """检查章节父级设置是否会形成循环。

    Args:
        chapter_id: 章节 ID。
        new_parent_id: 新父章节 ID。
        query_db: 数据库会话。

    Raises:
        ChapterLoopException: 会形成循环引用。
    """
    if new_parent_id == 0 or new_parent_id == chapter_id:
        # 根节点或自己作为父节点（虽然不应该，但不会形成循环）
        return

    # 检查 new_parent_id 的所有祖先节点中是否包含 chapter_id
    current_id = new_parent_id
    visited_ids = set()

    while current_id and current_id != 0:
        if current_id == chapter_id:
            raise ChapterLoopException(chapter_id=chapter_id, parent_id=new_parent_id)

        if current_id in visited_ids:
            # 检测到其他循环，不应该发生
            raise ChapterLoopException(chapter_id=chapter_id, parent_id=new_parent_id)

        visited_ids.add(current_id)
        chapter = await ChapterMapper.get_by_id(current_id, query_db)
        if not chapter:
            break
        current_id = chapter.parent_id


async def _get_all_descendant_ids(chapter_id: int, query_db: AsyncSession) -> list[int]:
    """获取章节的所有子孙节点 ID（包括自己）。

    Args:
        chapter_id: 章节 ID。
        query_db: 数据库会话。

    Returns:
        list[int]: 所有子孙节点 ID 列表。
    """
    from sqlalchemy import and_, select

    descendants = {chapter_id}
    to_check = [chapter_id]

    while to_check:
        current_id = to_check.pop()
        stmt = select(EduChapter).where(
            and_(
                EduChapter.parent_id == current_id,
                EduChapter.status != SystemConstants.Status.DELETED,
            )
        )
        children = (await query_db.execute(stmt)).scalars().all()
        for child in children:
            if child.chapter_id not in descendants:
                descendants.add(child.chapter_id)
                to_check.append(child.chapter_id)

    return list(descendants)


async def _get_children_count(chapter_id: int, query_db: AsyncSession) -> int:
    """获取章节的直接子节点数量。

    Args:
        chapter_id: 章节 ID。
        query_db: 数据库会话。

    Returns:
        int: 子节点数量。
    """
    from sqlalchemy import and_, func, select

    stmt = (
        select(func.count())
        .select_from(EduChapter)
        .where(
            and_(
                EduChapter.parent_id == chapter_id,
                EduChapter.status != SystemConstants.Status.DELETED,
            )
        )
    )
    result = await query_db.execute(stmt)
    return result.scalar() or 0


def _convert_chapter_orm_to_brief_vo(chapter_orm: EduChapter) -> ChapterTreeBriefVO:
    """将章节 ORM 对象转换为 ChapterTreeBriefVO（用于下拉选择）。

    Args:
        chapter_orm: 章节 ORM 对象。

    Returns:
        ChapterTreeBriefVO: 章节简要树形结构 VO。
    """
    return ChapterTreeBriefVO(
        chapter_id=chapter_orm.chapter_id,
        parent_id=chapter_orm.parent_id,
        chapter_name=chapter_orm.chapter_name,
        chapter_no=chapter_orm.chapter_no,
        children=[],
    )


def _build_chapter_brief_tree(chapter_list: list[EduChapter], parent_id: int = 0) -> list[ChapterTreeBriefVO]:
    """递归构建简要树形结构（用于下拉选择）。

    Args:
        chapter_list: 所有章节列表。
        parent_id: 父章节ID。

    Returns:
        list[ChapterTreeBriefVO]: 简要树形结构。
    """
    result: list[ChapterTreeBriefVO] = []

    # 过滤出当前父节点的直接子节点
    children = [ch for ch in chapter_list if ch.parent_id == parent_id]

    for chapter in children:
        vo = _convert_chapter_orm_to_brief_vo(chapter)
        # 递归构建子节点
        vo.children = _build_chapter_brief_tree(chapter_list, chapter.chapter_id)
        result.append(vo)

    return result


async def _check_chapter_permission(chapter_id: int, current_user: CurrentUser, query_db: AsyncSession) -> None:
    """检查用户是否有权限操作该章节。

    Args:
        chapter_id: 章节 ID。
        current_user: 当前用户。
        query_db: 数据库会话。

    Raises:
        ChapterNotFoundException: 章节不存在。
        ChapterNoPermissionException: 无权限。
    """
    # 管理员拥有全部权限
    if current_user.is_admin():
        return

    # 获取章节信息
    chapter = await ChapterMapper.get_by_id(chapter_id, query_db)
    if not chapter:
        raise ChapterNotFoundException(chapter_id=chapter_id)

    # 检查是否为教师
    if not current_user.detail or not current_user.detail.teacher_info:
        raise ChapterNoPermissionException(chapter_id=chapter_id)

    # 检查教师是否教授该课程
    from graphedu.mapper.education.course_teacher import CourseTeacherMapper

    teacher_id = current_user.detail.teacher_info.teacher_id
    course_teacher = await CourseTeacherMapper.get_by_ids(chapter.course_id, teacher_id, query_db)
    if not course_teacher:
        raise ChapterNoPermissionException(chapter_id=chapter_id)


# ============================================================================
# ChapterService 类
# ============================================================================


class ChapterService:
    """章节管理服务类

    提供章节的增删改查功能。
    """

    @staticmethod
    async def add_chapter(
        query_db: AsyncSession, chapter_data: ChapterCreateDTO, current_user: CurrentUser
    ) -> ChapterDetailVO:
        """新增章节信息。

        Args:
            query_db: 数据库会话。
            chapter_data: 新增章节 DTO。
            current_user: 当前登录用户。

        Returns:
            ChapterDetailVO: 创建成功的章节 VO。

        Raises:
            CourseNotFoundException: 课程不存在。
            ChapterNameAlreadyExistsException: 章节名称已存在。
            ChapterCreateFailedException: 章节新增失败。
        """
        # 1. 检查课程是否存在
        course = await CourseMapper.get_by_id(chapter_data.course_id, query_db)
        if not course:
            raise CourseNotFoundException(course_id=chapter_data.course_id)

        # 2. 如果有父章节，检查父章节是否存在
        if chapter_data.parent_id and chapter_data.parent_id != 0:
            parent_chapter = await ChapterMapper.get_by_id(chapter_data.parent_id, query_db)
            if not parent_chapter or parent_chapter.course_id != chapter_data.course_id:
                raise ChapterNotFoundException(chapter_id=chapter_data.parent_id)

        # 3. 校验章节名称唯一性（同一课程、同一父章节下）
        if await _check_chapter_name_exists(
            chapter_data.course_id, chapter_data.chapter_name, chapter_data.parent_id or 0, query_db
        ):
            raise ChapterNameAlreadyExistsException(chapter_name=chapter_data.chapter_name)

        # 4. DTO → ORM
        new_chapter = EduChapter(
            **chapter_data.model_dump(exclude_unset=True),
            parent_id=chapter_data.parent_id or 0,
            status=SystemConstants.Status.NORMAL,
            create_by=current_user.detail.user.user_id if current_user and current_user.detail.user else None,
            create_time=datetime.now(),
        )

        # 5. 新增章节
        try:
            await ChapterMapper.add_chapter(new_chapter, query_db)
        except Exception as e:
            logger.error(f"新增章节失败: {e}")
            raise ChapterCreateFailedException(chapter_name=chapter_data.chapter_name) from e

        logger.info(f"新增章节成功: {chapter_data.chapter_name}")

        # 6. 返回创建后的章节 VO
        return _convert_chapter_orm_to_detail_vo(new_chapter)

    @staticmethod
    async def update_chapter(
        query_db: AsyncSession, chapter_data: ChapterUpdateDTO, current_user: CurrentUser
    ) -> ChapterDetailVO:
        """更新章节信息。

        Args:
            query_db: 数据库会话。
            chapter_data: 更新章节 DTO。
            current_user: 当前登录用户。

        Returns:
            ChapterDetailVO: 更新后的章节 VO.

        Raises:
            ChapterNotFoundException: 章节不存在。
            ChapterNameAlreadyExistsException: 章节名称已存在。
            ChapterLoopException: 章节父级设置会形成循环。
            ChapterNoPermissionException: 无权限操作该章节。
            ChapterUpdateFailedException: 章节更新失败。
        """
        # 1. 获取目标章节
        target_chapter = await ChapterMapper.get_by_id(chapter_data.chapter_id, query_db)
        if not target_chapter:
            raise ChapterNotFoundException(chapter_id=chapter_data.chapter_id)

        # 2. 权限检查
        await _check_chapter_permission(chapter_data.chapter_id, current_user, query_db)

        # 3. 唯一性校验（章节名称）
        new_parent_id = chapter_data.parent_id if chapter_data.parent_id is not None else target_chapter.parent_id
        if chapter_data.chapter_name and chapter_data.chapter_name != target_chapter.chapter_name:  # noqa: SIM102
            if await _check_chapter_name_exists(
                target_chapter.course_id,
                chapter_data.chapter_name,
                new_parent_id,
                query_db,
                exclude_chapter_id=chapter_data.chapter_id,
            ):
                raise ChapterNameAlreadyExistsException(chapter_name=chapter_data.chapter_name)

        # 4. 检查是否会形成循环
        if chapter_data.parent_id is not None and chapter_data.parent_id != target_chapter.parent_id:
            await _check_chapter_loop(chapter_data.chapter_id, chapter_data.parent_id, query_db)

        # 5. 更新目标章节
        update_data = chapter_data.model_dump(exclude_unset=True, exclude={"chapter_id"})
        for field, value in update_data.items():
            if (field == "parent_id" and value is not None) or value is not None:
                setattr(target_chapter, field, value)

        target_chapter.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        target_chapter.update_time = datetime.now()

        try:
            await ChapterMapper.update(target_chapter, query_db)
        except Exception as e:
            logger.error(f"更新章节失败: {e}")
            raise ChapterUpdateFailedException(chapter_id=chapter_data.chapter_id) from e

        # 6. 返回更新后的章节 VO
        return _convert_chapter_orm_to_detail_vo(target_chapter)

    @staticmethod
    async def list_chapter(query_db: AsyncSession, query_object: ChapterQueryDTO) -> PageResponse[ChapterListVO]:
        """获取章节列表信息。

        Args:
            query_db: 数据库会话。
            query_object: 查询参数对象。

        Returns:
            PageResponse[ChapterListVO]: 分页结果。
        """
        rows, total = await ChapterMapper.get_chapter_list(query_db, query_object, is_page=True)

        # 将 ORM 对象转换为 ChapterListVO
        chapter_list = [_convert_chapter_orm_to_list_vo(row) for row in rows]

        return PageResponse(rows=chapter_list, page=query_object.page or 1, size=query_object.size or 10, total=total)

    @staticmethod
    async def delete_chapter(
        query_db: AsyncSession, chapter_id_list: list[int], current_user: CurrentUser
    ) -> BatchDeleteResponse[int]:
        """删除章节信息（批量，部分成功模式）。

        Args:
            query_db: 数据库会话。
            chapter_id_list: 章节 ID 列表。
            current_user: 当前用户。

        Returns:
            BatchDeleteResponse[int]: 包含成功数量、失败数量和详细结果的响应对象

        Raises:
            ChapterIdListEmptyException: 章节 ID 列表为空。
        """
        if not chapter_id_list:
            raise ChapterIdListEmptyException

        results: list[DeleteResultItem[int]] = []

        for chapter_id in chapter_id_list:
            try:
                # 权限检查
                await _check_chapter_permission(chapter_id, current_user, query_db)

                chapter = await ChapterMapper.get_by_id(chapter_id, query_db)
                if not chapter:
                    results.append(DeleteResultItem(target_id=chapter_id, success=False, error="章节不存在"))
                    continue

                # 检查是否有子章节
                children_count = await _get_children_count(chapter_id, query_db)
                if children_count > 0:
                    results.append(
                        DeleteResultItem(target_id=chapter_id, success=False, error="章节包含子章节，无法删除")
                    )
                    continue

                # 软删除章节
                chapter.status = SystemConstants.Status.DELETED
                chapter.update_by = current_user.detail.user.user_id if current_user.detail.user else None
                chapter.update_time = datetime.now()
                await ChapterMapper.update(chapter, query_db)

                results.append(DeleteResultItem(target_id=chapter_id, success=True, error=None))

            except ChapterNoPermissionException:
                results.append(DeleteResultItem(target_id=chapter_id, success=False, error="无权操作该章节"))
            except Exception as e:
                results.append(DeleteResultItem(target_id=chapter_id, success=False, error=str(e)))

        logger.info(
            f"批量删除章节完成: "
            f"{sum(1 for r in results if r.success)} 成功, "
            f"{sum(1 for r in results if not r.success)} 失败"
        )

        return BatchDeleteResponse.from_results(results)

    @staticmethod
    async def change_chapter_status(
        query_db: AsyncSession, chapter_id: int, status: str, current_user: CurrentUser
    ) -> None:
        """修改章节状态。

        Args:
            query_db: 数据库会话。
            chapter_id: 章节 ID。
            status: 状态。
            current_user: 当前用户。

        Raises:
            ChapterNotFoundException: 章节不存在。
            ChapterNoPermissionException: 无权限操作该章节。
        """
        # 权限检查
        await _check_chapter_permission(chapter_id, current_user, query_db)

        chapter = await ChapterMapper.get_by_id(chapter_id, query_db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)

        chapter.status = status
        chapter.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        chapter.update_time = datetime.now()
        await ChapterMapper.update(chapter, query_db)
        logger.info(f"修改章节状态成功: {chapter_id}")

    @staticmethod
    async def get_chapter_detail(query_db: AsyncSession, chapter_id: int) -> ChapterDetailVO | None:
        """获取章节详细信息。

        Args:
            query_db: 数据库会话。
            chapter_id: 章节 ID。

        Returns:
            ChapterDetailVO | None: 章节详细信息 VO。
        """
        chapter = await ChapterMapper.get_by_id(chapter_id, query_db)
        if not chapter:
            return None

        return _convert_chapter_orm_to_detail_vo(chapter)

    @staticmethod
    async def get_chapter_tree(query_db: AsyncSession, course_id: int) -> list[ChapterTreeVO]:
        """获取课程的章节树形结构。

        Args:
            query_db: 数据库会话。
            course_id: 课程 ID。

        Returns:
            list[ChapterTreeVO]: 章节树形结构。
        """
        # 通过 Mapper 获取所有章节（按 chapter_no 排序）
        chapters = await ChapterMapper.get_chapter_tree(course_id, query_db)

        # 转换为 VO 并构建树形结构
        chapter_map: dict[int, ChapterTreeVO] = {}
        for chapter in chapters:
            chapter_vo = _convert_chapter_orm_to_tree_vo(chapter)
            chapter_map[chapter.chapter_id] = chapter_vo

        root_chapters: list[ChapterTreeVO] = []
        for chapter in chapters:
            chapter_vo = chapter_map[chapter.chapter_id]
            if chapter.parent_id == 0 or chapter.parent_id not in chapter_map:
                root_chapters.append(chapter_vo)
            else:
                parent = chapter_map.get(chapter.parent_id)
                if parent:
                    if parent.children is None:
                        parent.children = []
                    parent.children.append(chapter_vo)

        return root_chapters

    @staticmethod
    async def get_chapter_tree_lazy(query_db: AsyncSession, course_id: int, parent_id: int = 0) -> list[ChapterTreeVO]:
        """获取课程的章节树形结构（懒加载模式）。

        Args:
            query_db: 数据库会话。
            course_id: 课程 ID。
            parent_id: 父章节ID（默认0表示根节点）。

        Returns:
            list[ChapterTreeVO]: 章节树形结构（扁平列表，带 has_children 标记）。
        """
        # 获取指定父节点的直接子节点
        chapters = await ChapterMapper.get_chapter_children(course_id, parent_id, query_db)

        # 转换为 VO 并设置 has_children 标记
        result: list[ChapterTreeVO] = []
        for chapter in chapters:
            has_children = await ChapterMapper.has_children(chapter.chapter_id, query_db)
            chapter_vo = _convert_chapter_orm_to_tree_vo(chapter, has_children=has_children)
            result.append(chapter_vo)

        return result

    @staticmethod
    async def get_chapter_tree_for_select(
        query_db: AsyncSession, course_id: int, parent_id: int = 0
    ) -> list[ChapterTreeBriefVO]:
        """获取课程的章节树形结构（下拉选择模式）。

        Args:
            query_db: 数据库会话。
            course_id: 课程 ID。
            parent_id: 父章节ID（默认0表示根节点，此参数用于兼容，实际返回完整树）。

        Returns:
            list[ChapterTreeBriefVO]: 章节完整树形结构（简要 VO）。
        """
        # 获取所有章节
        chapters = await ChapterMapper.get_chapter_tree(course_id, query_db)

        # 构建完整树形结构
        return _build_chapter_brief_tree(chapters, parent_id)

    @staticmethod
    async def move_chapter(
        query_db: AsyncSession, chapter_id: int, new_parent_id: int, new_chapter_no: int, current_user: CurrentUser
    ) -> None:
        """移动章节（修改父节点和序号）。

        Args:
            query_db: 数据库会话。
            chapter_id: 章节 ID。
            new_parent_id: 新父章节 ID。
            new_chapter_no: 新章节序号。
            current_user: 当前用户。

        Raises:
            ChapterNotFoundException: 章节不存在。
            ChapterLoopException: 章节父级设置会形成循环。
            ChapterNoPermissionException: 无权限操作该章节。
        """
        # 1. 检查目标章节
        target_chapter = await ChapterMapper.get_by_id(chapter_id, query_db)
        if not target_chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)

        # 2. 权限检查
        await _check_chapter_permission(chapter_id, current_user, query_db)

        # 3. 检查父章节是否存在（如果不是根节点）
        if new_parent_id != 0:
            parent_chapter = await ChapterMapper.get_by_id(new_parent_id, query_db)
            if not parent_chapter or parent_chapter.course_id != target_chapter.course_id:
                raise ChapterNotFoundException(chapter_id=new_parent_id)

        # 4. 检查是否会形成循环
        await _check_chapter_loop(chapter_id, new_parent_id, query_db)

        # 5. 更新章节
        target_chapter.parent_id = new_parent_id
        target_chapter.chapter_no = new_chapter_no
        target_chapter.update_by = current_user.detail.user.user_id if current_user.detail.user else None
        target_chapter.update_time = datetime.now()
        await ChapterMapper.update(target_chapter, query_db)

        logger.info(f"移动章节成功: {chapter_id} -> parent: {new_parent_id}, order: {new_chapter_no}")

    @staticmethod
    async def submit_generate_description(
        query_db: AsyncSession,
        chapter_id: int,
        graphrag_task_id: int,
        current_user: CurrentUser,
    ) -> ChapterDescriptionResultVO:
        """直接调用 GraphRAG Local Search 生成章节描述。

        检查章节是否存在，然后调用 GraphRAGService.generate_chapter_description
        并将结果写入 chapter.description。

        Args:
            query_db: 数据库会话。
            chapter_id: 章节 ID。
            graphrag_task_id: EduGraphRAGTask 主键 ID，用于定位该章节对应的构建任务。
            current_user: 当前用户。

        Returns:
            dict: 包含 description、chapter_id 的字典。

        Raises:
            ChapterNotFoundException: 章节不存在。
        """
        chapter = await ChapterMapper.get_by_id(chapter_id, query_db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)

        description = await GraphRAGService.generate_chapter_description(
            chapter.chapter_name, graphrag_task_id=graphrag_task_id
        )

        chapter.description = description
        await ChapterMapper.update(chapter, query_db)

        logger.info(
            "章节描述生成完毕，已写入 DB: chapter_id=%d, len=%d",
            chapter_id,
            len(description),
        )
        return ChapterDescriptionResultVO(
            description=description,
            chapter_id=chapter_id,
        )

    # ========================================================================
    # 知识点关联管理方法
    # ========================================================================

    @staticmethod
    async def link_knowledge_points(
        chapter_id: int,
        point_ids: list[str],
        db: AsyncSession,
    ) -> ChapterKnowledgePointLinkResultVO:
        """批量关联知识点到章节（跳过已存在，按传入顺序赋 sort_order）。

        Args:
            chapter_id: 章节ID。
            point_ids: 知识点节点ID列表（AGE 节点 ID 字符串）。
            db: SQLAlchemy 异步会话。

        Returns:
            ChapterKnowledgePointLinkResultVO: 关联结果

        Raises:
            ChapterNotFoundException: 章节不存在。
        """
        # 1. 验证章节存在
        chapter = await ChapterMapper.get_by_id(chapter_id, db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)

        # 2. 批量关联
        added = 0
        skipped = 0
        for point_id in point_ids:
            node_uuid = UUID(point_id)  # 转换字符串为 UUID
            existing = await ChapterKnowledgePointMapper.get_by_chapter_and_point(chapter_id, node_uuid, db)
            if existing:
                skipped += 1
                continue
            await ChapterKnowledgePointMapper.add_link(chapter_id, node_uuid, db)
            added += 1

        logger.info(f"章节 {chapter_id} 关联知识点成功: added={added}, skipped={skipped}")
        return ChapterKnowledgePointLinkResultVO(added=added, skipped=skipped)

    @staticmethod
    async def unlink_knowledge_point(
        chapter_id: int,
        point_id: str,
        db: AsyncSession,
    ) -> None:
        """解除章节与某个知识点的关联。

        Args:
            chapter_id: 章节ID。
            point_id: 知识点节点ID。
            db: SQLAlchemy 异步会话。

        Raises:
            ChapterNotFoundException: 章节不存在。
        """
        # 1. 验证章节存在
        chapter = await ChapterMapper.get_by_id(chapter_id, db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)

        # 2. 删除关联
        node_uuid = UUID(point_id)  # 转换字符串为 UUID
        rows = await ChapterKnowledgePointMapper.delete_link(chapter_id, node_uuid, db)
        if rows == 0:
            logger.warning(f"章节 {chapter_id} 与知识点 {node_uuid} 的关联不存在")
        else:
            logger.info(f"章节 {chapter_id} 解除知识点 {node_uuid} 关联成功")

    @staticmethod
    async def get_knowledge_points(
        chapter_id: int,
        db: AsyncSession,
        pg_client: AsyncPostgresqlClient,
    ) -> list[KnowledgeNodeChapterDetailVO]:
        """获取章节关联的知识点列表，并从知识图谱补充节点详情。

        Args:
            chapter_id: 章节ID。
            db: SQLAlchemy 异步会话。
            pg_client: PostgreSQL 异步客户端。

        Returns:
            list[KnowledgeNodeChapterDetailVO]: 关联列表（含知识点详情）。

        Raises:
            ChapterNotFoundException: 章节不存在。
        """
        # 1. 验证章节存在
        chapter = await ChapterMapper.get_by_id(chapter_id, db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)

        # 2. 获取关联列表并补充知识点详情
        from graphedu.services.education.syllabus_graph import SyllabusGraphService

        links = await ChapterKnowledgePointMapper.get_by_chapter(chapter_id, db)
        result: list[KnowledgeNodeChapterDetailVO] = []
        for link in links:
            node = await SyllabusGraphService.get_knowledge_point(pg_client, str(link.node_uuid))
            vo = KnowledgeNodeChapterDetailVO(
                node_chapter_id=link.node_chapter_id,
                chapter_id=link.chapter_id,
                node_uuid=str(link.node_uuid),
                relevance_score=link.relevance_score,
                description=link.description,
                is_primary=link.is_primary,
                status=link.status,
                create_by=link.create_by,
                create_time=link.create_time,
                update_by=link.update_by,
                update_time=link.update_time,
                node_title=node.title if node else None,
                node_description=node.description if node else None,
                node_importance=node.importance if node else None,
            )
            result.append(vo)
        return result

    @staticmethod
    async def clear_knowledge_points(chapter_id: int, db: AsyncSession) -> int:
        """清空章节的所有知识点关联。

        Args:
            chapter_id: 章节ID。
            db: SQLAlchemy 异步会话。

        Returns:
            int: 删除的关联数。

        Raises:
            ChapterNotFoundException: 章节不存在。
        """
        # 1. 验证章节存在
        chapter = await ChapterMapper.get_by_id(chapter_id, db)
        if not chapter:
            raise ChapterNotFoundException(chapter_id=chapter_id)

        # 2. 清空关联
        count = await ChapterKnowledgePointMapper.delete_all_by_chapter(chapter_id, db)
        logger.info(f"章节 {chapter_id} 清空知识点关联成功: {count} 条")
        return count

    # ========================================================================
    # 章节资源管理方法
    # ========================================================================

    @staticmethod
    async def add_resource(
        query_db: AsyncSession,
        resource_data,
        current_user: CurrentUser,
        s3_client,
    ) -> ChapterResourceDetailVO:
        """为章节添加资源（委托给 ChapterResourceService）。

        Args:
            query_db: 数据库会话。
            resource_data: 新增资源 DTO。
            current_user: 当前登录用户。
            s3_client: S3 客户端。

        Returns:
            ChapterResourceDetailVO: 创建成功的资源 VO。
        """
        from graphedu.services.education.chapter_resource import ChapterResourceService

        return await ChapterResourceService.add_chapter_resource(query_db, resource_data, current_user, s3_client)

    @staticmethod
    async def update_resource(
        query_db: AsyncSession,
        resource_data,
        current_user: CurrentUser,
        s3_client,
    ) -> ChapterResourceDetailVO:
        """更新章节资源（委托给 ChapterResourceService）。

        Args:
            query_db: 数据库会话。
            resource_data: 更新资源 DTO。
            current_user: 当前登录用户。
            s3_client: S3 客户端。

        Returns:
            ChapterResourceDetailVO: 更新后的资源 VO。
        """
        from graphedu.services.education.chapter_resource import ChapterResourceService

        return await ChapterResourceService.update_chapter_resource(query_db, resource_data, current_user, s3_client)

    @staticmethod
    async def delete_resources(
        query_db: AsyncSession, resource_id_list: list[int], current_user: CurrentUser
    ) -> ChapterResourceBatchDeleteResultVO:
        """删除章节资源（批量，委托给 ChapterResourceService）。

        Args:
            query_db: 数据库会话。
            resource_id_list: 资源 ID 列表。
            current_user: 当前用户。

        Returns:
            ChapterResourceBatchDeleteResultVO: 批量删除结果。
        """
        from graphedu.services.education.chapter_resource import ChapterResourceService

        response = await ChapterResourceService.delete_chapter_resource(query_db, resource_id_list, current_user)

        # 转换 DeleteResponse[int] 为 ChapterResourceBatchDeleteResultVO
        results = [
            {
                "resource_id": item.target_id,
                "success": item.success,
                "error": item.error,
            }
            for item in response.results
        ]

        return ChapterResourceBatchDeleteResultVO(
            success_count=response.success_count,
            fail_count=response.fail_count,
            results=results,
        )

    @staticmethod
    async def get_resources(
        query_db: AsyncSession, chapter_id: int, s3_client, include_hidden: bool = False
    ) -> list[ChapterResourceListVO]:
        """获取章节的资源列表（委托给 ChapterResourceService）。

        Args:
            query_db: 数据库会话。
            chapter_id: 章节 ID。
            s3_client: S3 客户端。
            include_hidden: 是否包含隐藏内容。

        Returns:
            list[ChapterResourceListVO]: 资源列表。
        """
        return await ChapterResourceService.get_resources_by_chapter(query_db, chapter_id, s3_client, include_hidden)

    @staticmethod
    async def reorder_resources(
        query_db: AsyncSession, chapter_id: int, resource_orders: dict[int, int], current_user: CurrentUser
    ) -> None:
        """调整章节资源顺序（委托给 ChapterResourceService）。

        Args:
            query_db: 数据库会话。
            chapter_id: 章节 ID。
            resource_orders: 资源 ID 到新序号的映射。
            current_user: 当前用户。
        """
        await ChapterResourceService.reorder_resources(query_db, chapter_id, resource_orders, current_user)

    @staticmethod
    async def change_resource_status(
        query_db: AsyncSession, resource_id: int, status: str, current_user: CurrentUser
    ) -> None:
        """修改资源状态（委托给 ChapterResourceService）。

        Args:
            query_db: 数据库会话。
            resource_id: 资源 ID。
            status: 状态。
            current_user: 当前用户。
        """
        await ChapterResourceService.change_resource_status(query_db, resource_id, status, current_user)
