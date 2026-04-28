/**
 * 代码生成工具相关类型定义
 * 对应后端：graphedu/api/services/tool/gen.py
 */

/**
 * 代码生成表查询参数
 */
export interface GenTableQueryDTO {
  /** 页码，从 1 开始 */
  page?: number
  /** 每页数量 */
  size?: number
  /** 表名称 */
  tableName?: string
  /** 表描述 */
  tableComment?: string
  /** 开始时间 */
  beginTime?: string
  /** 结束时间 */
  endTime?: string
  /** 排序字段 */
  orderByColumn?: string
  /** 是否升序 */
  isAsc?: string
}

/**
 * 代码生成表信息
 */
export interface GenTableVO {
  /** 表ID */
  tableId?: number
  /** 表名称 */
  tableName?: string
  /** 表描述 */
  tableComment?: string
  /** 实体类名称 */
  className?: string
  /** 创建时间 */
  createTime?: string
  /** 更新时间 */
  updateTime?: string
  /** 生成模板类型：crud-单表, tree-树表, sub-主子表 */
  tplCategory?: string
  /** 前端类型：element-ui, element-plus */
  tplWebType?: string
  /** 生成包路径 */
  packageName?: string
  /** 模块名 */
  moduleName?: string
  /** 业务名 */
  businessName?: string
  /** 功能名 */
  functionName?: string
  /** 生成作者 */
  functionAuthor?: string
  /** 生成方式：0-zip压缩包, 1-自定义路径 */
  genType?: string
  /** 生成路径 */
  genPath?: string
  /** 备注 */
  remark?: string
  /** 其他信息（JSON格式） */
  params?: GenTableParams
  /** 字段列表 */
  columns?: GenTableColumnVO[]
  /** 树编码字段 */
  treeCode?: string
  /** 树父编码字段 */
  treeParentCode?: string
  /** 树名称字段 */
  treeName?: string
  /** 上级菜单ID */
  parentMenuId?: number
  /** 关联子表的表名 */
  subTableName?: string
  /** 子表关联的外键名 */
  subTableFkName?: string
}

/**
 * 代码生成表参数
 */
export interface GenTableParams {
  /** 树编码字段 */
  treeCode?: string
  /** 树父编码字段 */
  treeParentCode?: string
  /** 树名称字段 */
  treeName?: string
  /** 上级菜单ID */
  parentMenuId?: number
  /** 关联子表的表名 */
  subTableName?: string
  /** 子表关联的外键名 */
  subTableFkName?: string
}

/**
 * 代码生成表字段信息
 */
export interface GenTableColumnVO {
  /** 字段ID */
  columnId?: number
  /** 表ID */
  tableId?: number
  /** 字段列名 */
  columnName?: string
  /** 字段描述 */
  columnComment?: string
  /** 物理类型 */
  columnType?: string
  /** Python类型 */
  pythonType?: string
  /** Python属性名 */
  pythonField?: string
  /** 是否插入（0-否，1-是） */
  isInsert?: string
  /** 是否编辑（0-否，1-是） */
  isEdit?: string
  /** 是否列表（0-否，1-是） */
  isList?: string
  /** 是否查询（0-否，1-是） */
  isQuery?: string
  /** 是否必填（0-否，1-是） */
  isRequired?: string
  /** 查询方式：EQ-等于, NE-不等于, GT-大于, GTE-大于等于, LT-小于, LTE-小于等于, LIKE-模糊查询, BETWEEN-范围查询 */
  queryType?: string
  /** 显示类型：input-文本框, textarea-文本域, select-下拉框, radio-单选框, checkbox-复选框, datetime-日期控件, imageUpload-图片上传, fileUpload-文件上传, editor-富文本控件 */
  htmlType?: string
  /** 字典类型 */
  dictType?: string
  /** 排序 */
  sort?: number
}

/**
 * 代码生成详情响应
 */
export interface GenTableDetailVO {
  /** 表信息 */
  info: GenTableVO
  /** 字段列表 */
  rows: GenTableColumnVO[]
  /** 其他表信息（用于主子表） */
  tables?: GenTableVO[]
}

/**
 * 代码预览响应
 */
export type GenCodePreviewVO = Record<string, string>

/**
 * 数据库表查询参数
 */
export interface DbTableQueryDTO {
  /** 页码，从 1 开始 */
  page?: number
  /** 每页数量 */
  size?: number
  /** 表名称 */
  tableName?: string
  /** 表描述 */
  tableComment?: string
}

/**
 * 数据库表信息
 */
export interface DbTableVO {
  /** 表名称 */
  tableName?: string
  /** 表描述 */
  tableComment?: string
  /** 创建时间 */
  createTime?: string
  /** 更新时间 */
  updateTime?: string
}

/**
 * 导入表请求参数
 */
export interface ImportTableDTO {
  /** 表名称列表 */
  tableNames: string
}

/**
 * 创建表请求参数
 */
export interface CreateTableDTO {
  /** 建表SQL语句 */
  sql: string
}

/**
 * 更新代码生成配置请求
 */
export interface UpdateGenTableDTO extends GenTableVO {
  /** 表ID（必填） */
  tableId: number
  /** 字段列表（必填） */
  columns: GenTableColumnVO[]
}

/**
 * 字典选项
 */
export interface DictOptionVO {
  /** 字典类型 */
  dictType?: string
  /** 字典名称 */
  dictName?: string
}

/**
 * 菜单树选项
 */
export interface MenuTreeOptionVO {
  /** 菜单ID */
  functionId?: number
  /** 菜单名称 */
  functionName?: string
  /** 子菜单 */
  children?: MenuTreeOptionVO[]
}
