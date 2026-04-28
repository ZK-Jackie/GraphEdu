"""Apache AGE 图数据库节点定义

Apache AGE 节点和关系不通过 SQLAlchemy ORM 管理，
而是通过 `graphedu.common.resource.modules.graph_db.age.AgeClient`
直接执行 Cypher 语句进行增删改查。

大纲图谱（SKG）节点与关系类型（在 AGE 图 edu_knowledge_graph 中）：

节点类型:
  - KnowledgePoint  属性: id, course_id, title, description, importance(1-5), source

关系类型:
  - PREREQUISITE    属性: confidence(0.0-1.0), source
  - RELATED_TO      属性: confidence(0.0-1.0)
"""
