# DTO/VO → TypeScript 转换规范

## 概述

扫描 Python 后端的路由定义及相关的数据模型 (DTO/VO),自动在前端项目中生成对应的 TypeScript 类型定义文件 (`.ts`) 和 API 请求函数。

包含完整的命名转换 (snake_case 转 camelCase) 和类型映射规则,确保前后端类型的一致性。

## 输入参数

- `backendModulePath` (必选): 后端模块路径,相对于项目根目录。例如: `graphedu/api/services/system`
- `frontendTypesDir` (可选): 前端类型存储目录。默认为: `graphedu-ui/src/types/modules`
- `frontendApiDir` (可选): 前端 API 函数存储目录。默认为: `graphedu-ui/src/api`

## 执行流程

### 1. 扫描并分析后端 API 结构

使用 `glob` 工具扫描 `backendModulePath` 下的所有 `*.py` 文件:

**识别路由装饰器**:
```python
@router.get("/list")
@router.post("/")
@router.put("/{id}")
@router.delete("/{ids}")
```

**提取信息**:
- HTTP 方法 (GET/POST/PUT/DELETE)
- 路由路径 (`/list`, `/{id}`)
- 路径参数 (`id`)
- 请求体类型 (DTO)
- 响应类型 (VO)

### 2. 读取 DTO 和 VO 定义

根据后端代码中的导入路径,定位 DTO 和 VO 的定义文件:

**导入路径示例**:

```python
from graphedu.common.models.dto.systemv2.user import UserCreateDTO, UserUpdateDTO
from graphedu.common.models.vo.systemv2.user import UserDetailVO, UserListVO
```

**定位文件**:
- DTO 通常位于: `graphedu/common/models/dto/{module}.py`
- VO 通常位于: `graphedu/common/models/vo/{module}.py`

**解析内容**:
- 读取类定义和字段注解
- 提取 `Field(description="...")` 描述信息
- 识别类型注解 (`str | None`, `list[int]`, `datetime`)

### 3. 确认同步模式

在生成文件前,询问用户选择同步模式:

- **覆盖模式**: 删除现有的前端类型和 API 文件,完全重新生成 (适用于大版本更新)
- **增量模式**: 保留现有文件,仅添加缺失的类型和函数 (适用于日常开发)

### 4. 执行类型转换与命名规范化

应用以下规则将 Python 定义转换为 TypeScript 定义。

## 字段命名转换 (snake_case → camelCase)

| Python (后端)       | TypeScript (前端) | 说明       |
|-------------------|------------------|-----------|
| `user_name`       | `userName`       | 普通字段    |
| `user_id`         | `userId`         | ID 字段   |
| `role_ids`        | `roleIds`        | 列表/数组字段 |
| `create_time`     | `createTime`     | 时间字段    |
| `avatar_file_id`  | `avatarFileId`   | 多词字段   |
| `dept_id`         | `deptId`         | 部门字段   |

**转换规则**:
```python
# Python
user_name: str
role_ids: list[int]
avatar_file_id: int | None

# TypeScript
userName: string
roleIds: number[]
avatarFileId?: number  // 可选字段添加 ?
```

## 基础类型映射 (Python → TypeScript)

| Python 类型                     | TypeScript 类型            | 备注              |
|-------------------------------|--------------------------|------------------|
| `str`                         | `string`                 |                  |
| `int`                         | `number`                 |                  |
| `float`                       | `number`                 |                  |
| `bool`                        | `boolean`                |                  |
| `list[T]`                     | `T[]`                    | 泛型数组           |
| `dict`                        | `Record<string, any>`    | 字典类型          |
| `datetime`                    | `string`                 | ISO 8601 格式    |
| `T \| None` / `Optional[T]`   | `T` (添加 `?` 可选标记)     | 可选字段        |
| `Literal['0', '1']`           | `'0' \| '1'`             | 字面量类型        |
| `PageResponse[T]`             | `PageResponse<T>`        | 分页响应         |

### 特殊类型处理

**分页响应**:
```python
# Python
class PageResponse(BaseModel):
    total: int
    items: list[T]

# TypeScript
export interface PageResponse<T> {
    total: number
    items: T[]
}
```

**通用响应**:
```python
# Python
class ResponseType(BaseModel):
    code: str
    data: T
    msg: str

# TypeScript
export interface ResponseType<T> {
    code: string
    data: T
    msg: string
}
```

## 路由到函数名映射

| 后端路由        | 方法   | 前端函数名              | 示例                          |
|---------------|-------|---------------------|-----------------------------|
| `/list`       | GET   | `getXxxList`        | `getUserList`               |
| `/{id}`       | GET   | `getXxxDetail`      | `getUserDetail`             |
| `` (根)       | POST  | `addXxx`            | `addUser`                   |
| `` (根)       | PUT   | `updateXxx`         | `updateUser`                |
| `/{ids}`      | DELETE| `deleteXxx`         | `deleteUser`                |
| `/status`     | PUT   | `changeXxxStatus`   | `changeUserStatus`          |
| `/password`   | PUT   | `resetXxxPassword`  | `resetUserPassword`         |

**命名规则**:
- GET 查询: `get` + 实体名 + 类型 (`List`, `Detail`)
- POST 创建: `add` + 实体名
- PUT 更新: `update` + 实体名
- DELETE 删除: `delete` + 实体名
- PUT 特殊操作: `change` + 实体名 + 操作名

## 类型定义文件模板

**文件路径**: `{frontendTypesDir}/{module}.ts`

```typescript
/**
 * {模块名称} 类型定义
 * @description 对应后端: graphedu/common/models/dto/{module}.py, graphedu/common/models/vo/{module}.py
 */

// ================== 请求 DTO ==================

/**
 * {DTO描述}
 */
export interface {Xxx}DTO {
    /** {字段描述} */
    {field_name}?: {field_type}

    /** {字段描述} */
    {field_name}: {field_type}
}

// ================== 响应 VO ==================

/**
 * {VO描述}
 */
export interface {Xxx}VO {
    /** {字段描述} */
    {field_name}: {field_type}

    /** {字段描述} */
    {field_name}?: {field_type}
}
```

### 类型定义示例

```typescript
/**
 * 用户类型定义
 * @description 对应后端: graphedu/common/models/dto/user.py, graphedu/common/models/vo/user.py
 */

// ================== 请求 DTO ==================

/**
 * 创建用户 DTO
 */
export interface UserCreateDTO {
    /** 用户账号 */
    user_name: string

    /** 用户昵称 */
    nick_name: string

    /** 用户密码 */
    password: string

    /** 用户邮箱 */
    email?: string

    /** 手机号码 */
    phonenumber?: string

    /** 用户类型: 1-学生, 2-教师, 3-管理员 */
    user_type?: string

    /** 帐号状态（0正常 1停用）*/
    status?: '0' | '1'

    /** 备注 */
    remark?: string

    /** 角色ID列表 */
    role_ids?: number[]

    /** 部门ID列表 */
    dept_ids?: number[]
}

/**
 * 用户查询 DTO
 */
export interface UserQueryDTO extends PageQueryDTO {
    /** 用户ID */
    user_id?: number

    /** 用户账号 */
    user_name?: string

    /** 用户昵称 */
    nick_name?: string

    /** 帐号状态（0正常 1停用）*/
    status?: '0' | '1'

    /** 角色ID列表 */
    role_ids?: number[]

    /** 部门ID列表 */
    dept_ids?: number[]

    /** 创建开始时间 */
    begin_time?: string

    /** 创建结束时间 */
    end_time?: string
}

// ================== 响应 VO ==================

/**
 * 用户详细信息 VO
 */
export interface UserDetailVO {
    /** 用户ID */
    user_id: number

    /** 登录账号 */
    user_name: string

    /** 用户昵称 */
    nick_name: string

    /** 用户邮箱 */
    email?: string

    /** 手机号码 */
    phonenumber?: string

    /** 头像文件ID */
    avatar_file_id?: number

    /** 用户类型: 1-学生, 2-教师, 3-管理员 */
    user_type: string

    /** 帐号状态（0正常 1停用）*/
    status: string

    /** 最后登录IP */
    login_ip?: string

    /** 最后登录时间 */
    login_date?: string

    /** 创建时间 */
    create_time?: string

    /** 更新时间 */
    update_time?: string

    /** 备注 */
    remark?: string

    /** 部门ID列表 */
    dept_ids?: number[]

    /** 角色ID列表 */
    role_ids?: number[]
}

/**
 * 用户列表项 VO
 */
export interface UserListVO {
    /** 用户ID */
    user_id: number

    /** 登录账号 */
    user_name: string

    /** 用户昵称 */
    nick_name: string

    /** 用户邮箱 */
    email?: string

    /** 手机号码 */
    phonenumber?: string

    /** 头像文件ID */
    avatar_file_id?: number

    /** 用户类型: 1-学生, 2-教师, 3-管理员 */
    user_type: string

    /** 帐号状态（0正常 1停用）*/
    status: string

    /** 创建时间 */
    create_time?: string

    /** 主部门ID */
    dept_id?: number

    /** 主部门名称 */
    dept_name?: string
}
```

## API 接口文件模板

**文件路径**: `{frontendApiDir}/{module}.ts`

```typescript
/**
 * {模块名称} API
 * @description 对应后端: graphedu/api/services/{path}/{module}.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/modules/common'
import type { {Xxx}DTO, {Xxx}VO, {Xxx}QueryDTO } from '@/types/modules/{module}'

/**
 * {接口描述}
 * @url {route}
 */
export function {functionName}(data: {Xxx}DTO): Promise<ResponseType<{Xxx}VO>> {
    return request({
        url: '{route}',
        method: '{http_method}',
        data: data // POST/PUT 用 data, GET/DELETE 用 params
    })
}
```

### 请求参数处理规范

**GET/DELETE 请求**:
```typescript
// 查询参数放在 params 字段
export function getUserList(params: UserQueryDTO): Promise<ResponseType<PageResponse<UserListVO>>> {
    return request({
        url: '/system/user/list',
        method: 'get',
        params: params
    })
}
```

**POST/PUT 请求**:
```typescript
// 请求体放在 data 字段
export function addUser(data: UserCreateDTO): Promise<ResponseType<Empty>> {
    return request({
        url: '/system/user',
        method: 'post',
        data: data
    })
}
```

**路径参数**:
```typescript
// 使用模板字符串拼接 URL
export function deleteUser(userIds: number[]): Promise<ResponseType<Empty>> {
    return request({
        url: `/system/user/${userIds.join(',')}`,
        method: 'delete'
    })
}

export function getUserDetail(userId: number): Promise<ResponseType<UserDetailVO>> {
    return request({
        url: `/system/user/${userId}`,
        method: 'get'
    })
}
```

### API 函数示例

```typescript
/**
 * 用户 API
 * @description 对应后端: graphedu/api/services/system/user.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/modules/common'
import type {
    UserCreateDTO,
    UserUpdateDTO,
    UserQueryDTO,
    UserDetailVO,
    UserListVO,
    UserStatusChangeDTO
} from '@/types/modules/user'

/**
 * 查询用户列表
 * @url /system/user/list
 */
export function getUserList(params: UserQueryDTO): Promise<ResponseType<PageResponse<UserListVO>>> {
    return request({
        url: '/system/user/list',
        method: 'get',
        params: params
    })
}

/**
 * 查询用户详细
 * @url /system/user/{id}
 */
export function getUserDetail(userId: number): Promise<ResponseType<UserDetailVO>> {
    return request({
        url: `/system/user/${userId}`,
        method: 'get'
    })
}

/**
 * 新增用户
 * @url /system/user
 */
export function addUser(data: UserCreateDTO): Promise<ResponseType<Empty>> {
    return request({
        url: '/system/user',
        method: 'post',
        data: data
    })
}

/**
 * 修改用户
 * @url /system/user
 */
export function updateUser(data: UserUpdateDTO): Promise<ResponseType<Empty>> {
    return request({
        url: '/system/user',
        method: 'put',
        data: data
    })
}

/**
 * 删除用户
 * @url /system/user/{ids}
 */
export function deleteUser(userIds: number[]): Promise<ResponseType<Empty>> {
    return request({
        url: `/system/user/${userIds.join(',')}`,
        method: 'delete'
    })
}

/**
 * 修改用户状态
 * @url /system/user/status
 */
export function changeUserStatus(data: UserStatusChangeDTO): Promise<ResponseType<Empty>> {
    return request({
        url: '/system/user/status',
        method: 'put',
        data: data
    })
}
```

## 导入顺序规范

TypeScript 文件的导入应遵循以下顺序:

1. **工具函数导入**:
   ```typescript
   import request from '@/utils/request'
   ```

2. **通用类型导入**:
   ```typescript
   import type { ResponseType, PageResponse, Empty } from '@/types/modules/common'
   ```

3. **当前模块类型导入**:
   ```typescript
   import type { UserCreateDTO, UserDetailVO } from '@/types/modules/user'
   ```

## 注释规范

### 文件头注释

**类型文件**:
```typescript
/**
 * 用户类型定义
 * @description 对应后端: graphedu/common/models/dto/user.py, graphedu/common/models/vo/user.py
 */
```

**API 文件**:
```typescript
/**
 * 用户 API
 * @description 对应后端: graphedu/api/services/system/user.py
 */
```

### 函数注释

每个 API 函数必须包含 JSDoc 注释:

```typescript
/**
 * 查询用户列表
 * @url /system/user/list
 * @description 分页查询用户信息,支持按用户名、昵称、邮箱、手机号等条件查询
 */
export function getUserList(params: UserQueryDTO): Promise<ResponseType<PageResponse<UserListVO>>> {
    // ...
}
```

### 字段注释

每个接口字段必须包含 JSDoc 注释:

```typescript
export interface UserCreateDTO {
    /** 用户账号 */
    user_name: string

    /** 用户昵称 */
    nick_name: string

    /** 用户密码 */
    password: string
}
```

## 特殊场景处理

### 跳过 Token 认证

如果接口需要跳过 Token 认证 (如登录、注册接口):

```typescript
export function login(data: LoginDTO): Promise<ResponseType<LoginResponseDTO>> {
    return request({
        url: '/auth/login',
        method: 'post',
        data: data,
        headers: {
            skipToken: true  // 跳过 Token 认证
        }
    })
}
```

### 分页列表返回类型

统一使用 `PageResponse<ItemVO>` 作为返回类型:

```typescript
export function getUserList(params: UserQueryDTO): Promise<ResponseType<PageResponse<UserListVO>>> {
    // ...
}

export function getRoleList(params: RoleQueryDTO): Promise<ResponseType<PageResponse<RoleListVO>>> {
    // ...
}
```

### 文件上传

```typescript
/**
 * 上传文件
 * @url /system/upload
 */
export function uploadFile(file: File): Promise<ResponseType<UploadVO>> {
    const formData = new FormData()
    formData.append('file', file)

    return request({
        url: '/system/upload',
        method: 'post',
        data: formData,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}
```

### 文件下载

```typescript
/**
 * 下载文件
 * @url /system/download/{id}
 */
export function downloadFile(fileId: number): Promise<Blob> {
    return request({
        url: `/system/download/${fileId}`,
        method: 'get',
        responseType: 'blob'
    })
}
```

## 文件组织

### 目录结构

```
graphedu-ui/src/
├── types/
│   ├── modules/
│   │   ├── common.ts      # 通用类型
│   │   ├── user.ts        # 用户类型
│   │   ├── role.ts        # 角色类型
│   │   └── dept.ts        # 部门类型
│   └── index.ts           # 类型导出
└── api/
    ├── user.ts            # 用户 API
    ├── role.ts            # 角色 API
    └── dept.ts            # 部门 API
```

### 命名约定

- **类型文件名**: 与后端模块同名 (如 `user.ts`, `role.ts`)
- **API 文件名**: 与后端控制器同名 (如 `user.py` → `user.ts`)
- **接口命名**: DTO/VO 保持后端命名 (如 `UserCreateDTO`, `UserDetailVO`)
- **函数命名**: 驼峰命名,见 "路由到函数名映射" 表

## 注意事项

### ⚠️ 文件一致性

- 前端文件名必须与后端模块名保持一致 (例如 `user.py` → `user.ts`)
- 如果后端模块拆分多个文件,前端也应拆分对应文件

### ⚠️ 类型导出

建议在 `types/index.ts` 中统一导出所有类型:

```typescript
export * from './modules/common'
export * from './modules/user'
export * from './modules/role'
```

这样在使用时可以:
```typescript
import type { UserCreateDTO, UserDetailVO } from '@/types'
```

### ⚠️ 可选字段处理

**Python 可选字段** (`field: str | None`) → **TypeScript 可选字段** (`field?: string`)

```typescript
// Python
email: str | None = Field(default=None, description="邮箱")

// TypeScript
email?: string  // 自动添加 ?
```

### ⚠️ 字面量类型

Python 的 `Literal['0', '1']` 应转换为 TypeScript 的联合类型:

```typescript
// Python
status: Literal["0", "1"] = Field(description="状态")

// TypeScript
status: '0' | '1'  // 联合字面量类型
```

### ⚠️ 泛型处理

Python 的 `list[int]` 应转换为 TypeScript 的数组类型:

```typescript
// Python
role_ids: list[int]

// TypeScript
role_ids: number[]  // 数组类型
```

## 完整示例

### 后端 API (graphedu/api/services/system/user.py)

```python
from fastapi import APIRouter, Depends
from graphedu.common.models.dto.systemv2.user import UserCreateDTO, UserQueryDTO
from graphedu.common.models.vo.systemv2.user import UserDetailVO, UserListVO
from graphedu.common.models.base import PageResponse

router = APIRouter(prefix="/system/user", tags=["用户管理"])


@router.get("/list", response_model=ResponseType[PageResponse[UserListVO]])
async def get_user_list(
        query: UserQueryDTO = Depends(),
        service: UserService = Depends(get_user_service)
):
    """查询用户列表"""
    return await service.list(query)


@router.post("/", response_model=ResponseType[UserDetailVO])
async def add_user(
        data: UserCreateDTO,
        service: UserService = Depends(get_user_service)
):
    """新增用户"""
    return await service.create(data)
```

### 生成的 TypeScript 类型 (graphedu-ui/src/types/modules/user.ts)

```typescript
/**
 * 用户类型定义
 * @description 对应后端: graphedu/common/models/dto/user.py, graphedu/common/models/vo/user.py
 */

export interface UserQueryDTO {
    /** 用户ID */
    user_id?: number

    /** 用户账号 */
    user_name?: string

    /** 用户昵称 */
    nick_name?: string

    /** 帐号状态（0正常 1停用）*/
    status?: '0' | '1'
}

export interface UserCreateDTO {
    /** 用户账号 */
    user_name: string

    /** 用户昵称 */
    nick_name: string

    /** 用户密码 */
    password: string
}

export interface UserListVO {
    /** 用户ID */
    user_id: number

    /** 登录账号 */
    user_name: string

    /** 用户昵称 */
    nick_name: string

    /** 帐号状态（0正常 1停用）*/
    status: string
}

export interface UserDetailVO {
    /** 用户ID */
    user_id: number

    /** 登录账号 */
    user_name: string

    /** 用户昵称 */
    nick_name: string

    /** 帐号状态（0正常 1停用）*/
    status: string
}
```

### 生成的 API 函数 (graphedu-ui/src/api/user.ts)

```typescript
/**
 * 用户 API
 * @description 对应后端: graphedu/api/services/system/user.py
 */
import request from '@/utils/request'
import type { ResponseType, PageResponse, Empty } from '@/types/modules/common'
import type { UserCreateDTO, UserQueryDTO, UserDetailVO, UserListVO } from '@/types/modules/user'

/**
 * 查询用户列表
 * @url /system/user/list
 */
export function getUserList(params: UserQueryDTO): Promise<ResponseType<PageResponse<UserListVO>>> {
    return request({
        url: '/system/user/list',
        method: 'get',
        params: params
    })
}

/**
 * 新增用户
 * @url /system/user
 */
export function addUser(data: UserCreateDTO): Promise<ResponseType<UserDetailVO>> {
    return request({
        url: '/system/user',
        method: 'post',
        data: data
    })
}
```