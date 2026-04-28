"""课程评价管理 Mapper 层

负责课程评价数据的访问操作，包括课程评价的增删改查等功能。
"""

from collections.abc import Sequence
from datetime import datetime, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from graphedu.common.models import SystemConstants
from graphedu.common.models.dto.educationv2.course_review import CourseReviewQueryDTO
from graphedu.common.models.orm.education import EduCourseReview


class CourseReviewMapper:
    """课程评价数据访问层

    提供课程评价的 CRUD 操作。
    """

    @staticmethod
    async def add_course_review(review_info: EduCourseReview, db_session: AsyncSession) -> EduCourseReview:
        """添加课程评价

        :param db_session: 数据库会话
        :param review_info: 课程评价信息
        :return: 课程评价对象
        """
        db_session.add(review_info)
        await db_session.flush()
        return review_info

    @staticmethod
    async def get_by_id(review_id: int, db_session: AsyncSession) -> EduCourseReview | None:
        """根据评价ID查询课程评价信息

        :param db_session: 数据库会话
        :param review_id: 评价ID
        :return: 课程评价对象
        """
        stmt = select(EduCourseReview).where(
            EduCourseReview.review_id == review_id, EduCourseReview.status != SystemConstants.Status.DELETED
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_by_student_and_course(
        student_id: int, course_id: int, db_session: AsyncSession
    ) -> EduCourseReview | None:
        """根据学生ID和课程ID查询评价

        :param db_session: 数据库会话
        :param student_id: 学生ID
        :param course_id: 课程ID
        :return: 课程评价对象
        """
        stmt = select(EduCourseReview).where(
            and_(
                EduCourseReview.student_id == student_id,
                EduCourseReview.course_id == course_id,
                EduCourseReview.status != SystemConstants.Status.DELETED,
            )
        )
        return (await db_session.execute(stmt)).scalars().first()

    @staticmethod
    async def get_review_list(
        db: AsyncSession, query_object: CourseReviewQueryDTO, is_page: bool = False
    ) -> tuple[Sequence[EduCourseReview], int]:
        """根据查询参数获取课程评价列表信息

        :param db: 数据库会话
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: (rows, total) 元组
        """
        # 构建基础查询条件
        base_conditions = [EduCourseReview.status != SystemConstants.Status.DELETED]

        if query_object.review_id is not None:
            base_conditions.append(EduCourseReview.review_id == query_object.review_id)
        if query_object.course_id is not None:
            base_conditions.append(EduCourseReview.course_id == query_object.course_id)
        if query_object.student_id is not None:
            base_conditions.append(EduCourseReview.student_id == query_object.student_id)
        if query_object.rating is not None:
            base_conditions.append(EduCourseReview.rating == query_object.rating)
        if query_object.is_visible:
            base_conditions.append(EduCourseReview.is_visible == query_object.is_visible)
        if query_object.status:
            base_conditions.append(EduCourseReview.status == query_object.status)
        if query_object.begin_time and query_object.end_time:
            base_conditions.append(
                EduCourseReview.create_time.between(
                    datetime.combine(query_object.begin_time, time(0, 0, 0)),
                    datetime.combine(query_object.end_time, time(23, 59, 59)),
                )
            )

        # 构建查询
        query = select(EduCourseReview).where(and_(*base_conditions)).order_by(EduCourseReview.create_time.desc())

        # 获取总数
        count_query = select(func.count()).select_from(EduCourseReview).where(and_(*base_conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        if is_page and query_object.page and query_object.size:
            offset = (query_object.page - 1) * query_object.size
            query = query.offset(offset).limit(query_object.size)

        result = await db.execute(query)
        rows = result.scalars().all()

        return rows, total

    @staticmethod
    async def get_reviews_by_course_id(course_id: int, db_session: AsyncSession) -> list[EduCourseReview]:
        """根据课程ID获取所有可见评价列表

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :return: 评价列表
        """
        stmt = (
            select(EduCourseReview)
            .where(
                and_(
                    EduCourseReview.course_id == course_id,
                    EduCourseReview.is_visible == "Y",
                    EduCourseReview.status != SystemConstants.Status.DELETED,
                )
            )
            .order_by(EduCourseReview.create_time.desc())
        )
        result = await db_session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update(review_info: EduCourseReview, query_db: AsyncSession) -> None:
        """更新课程评价信息

        :param query_db: 数据库会话
        :param review_info: 课程评价信息
        :return: None
        """
        await query_db.merge(review_info)
        await query_db.flush()

    @staticmethod
    async def delete_course_review(review_id: int, query_db: AsyncSession) -> None:
        """根据评价ID软删除课程评价

        :param query_db: 数据库会话
        :param review_id: 评价ID
        :return: None
        """
        review = await CourseReviewMapper.get_by_id(review_id, query_db)
        if review:
            review.status = SystemConstants.Status.DELETED
            await CourseReviewMapper.update(review, query_db)

    @staticmethod
    async def increment_like_count(review_id: int, query_db: AsyncSession) -> None:
        """增加评价点赞数

        :param query_db: 数据库会话
        :param review_id: 评价ID
        :return: None
        """
        review = await CourseReviewMapper.get_by_id(review_id, query_db)
        if review:
            review.like_count = (review.like_count or 0) + 1
            await CourseReviewMapper.update(review, query_db)

    @staticmethod
    async def get_course_rating_stats(course_id: int, db_session: AsyncSession) -> dict:
        """获取课程评分统计信息

        :param db_session: 数据库会话
        :param course_id: 课程ID
        :return: 评分统计字典
        """
        # 获取所有可见评价
        stmt = select(EduCourseReview).where(
            and_(
                EduCourseReview.course_id == course_id,
                EduCourseReview.is_visible == "Y",
                EduCourseReview.status != SystemConstants.Status.DELETED,
            )
        )
        result = await db_session.execute(stmt)
        reviews = list(result.scalars().all())

        if not reviews:
            return {"count": 0, "average_rating": 0.0, "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}}

        total_rating = sum(r.rating for r in reviews)
        count = len(reviews)

        # 统计各星级评价数量
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_distribution[review.rating] += 1

        return {
            "count": count,
            "average_rating": round(total_rating / count, 1),
            "rating_distribution": rating_distribution,
        }
