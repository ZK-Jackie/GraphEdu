# Type Error Patterns and Fix Strategies

## Table of Contents

- [Error Message Patterns](#error-message-patterns)
  - [A. Data Model Mismatch](#a-data-model-mismatch)
  - [B. Import Errors](#b-import-errors)
  - [C. Vue Component](#c-vue-component)
  - [D. API Response Typing](#d-api-response-typing)
  - [E. General TS](#e-general-ts)
- [Backend File Mapping](#backend-file-mapping)
- [Quick Fix Templates](#quick-fix-templates)

## Error Message Patterns

### A. Data Model Mismatch

**TS2322: Type 'X' is not assignable to type 'Y'**
- In `types/api/**/*.ts`: field type doesn't match usage. Check backend VO/DTO.
- Example: `Type 'string' is not assignable to type 'number'` → backend changed field type.

**TS2551: Property 'X' does not exist on type 'Y'. Did you mean 'Z'?**
- In `types/api/**/*.ts`: field name mismatch or field added/removed on backend.

**TS2561: Object is of type 'unknown'**
- Often when API response type is not properly narrowed. Add type annotation.

### B. Import Errors

**TS2307: Cannot find module '@/types/api/xxx'**
- Check file exists and path is correct.

**TS2305: Module '"@/types/api/xxx"' has no exported member 'YyyVO'**
- Type not exported. Add `export` keyword or check correct file.

**TS2614: Module '"..."' has no exported member 'X'. Did you mean to use 'import type'?**
- Change `import { X }` to `import type { X }`.

### C. Vue Component

**TS2322: Type 'X' is not assignable to type 'IntrinsicAttributes & ...'**
- Component props don't match. Check `defineProps` definition.

**TS2554: Expected N arguments, but got M**
- Emit call signature doesn't match `defineEmits` definition.

### D. API Response Typing

**TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'**
- API function parameter type doesn't match the caller's argument.

**TS2339: Property 'data' does not exist on type 'Promise<...>'**
- Missing `await` or incorrect return type on API function.

### E. General TS

**TS2531: Object is possibly 'null' or 'undefined'**
- Add optional chaining `?.`, nullish coalescing `??`, or explicit null check.

**TS2339: Property 'X' does not exist on type 'Y'**
- Missing property. Add to interface or use type assertion if appropriate.

**TS2790: The operand of a 'delete' operator must be optional**
- Field being deleted is required. Make it optional first.

**TS4111: Property 'X' comes from an index signature that is read-only**
- Attempting to mutate a readonly property. Use spread instead.

## Backend File Mapping

When data model mismatch is detected, locate the backend source:

| Frontend file | Backend VO | Backend DTO |
|--------------|-----------|------------|
| `types/api/system/user.ts` | `graphedu/common/models/vo/systemv2/user.py` | `graphedu/common/models/dto/systemv2/user.py` |
| `types/api/system/role.ts` | `vo/systemv2/role.py` | `dto/systemv2/role.py` |
| `types/api/system/dept.ts` | `vo/systemv2/dept.py` | `dto/systemv2/dept.py` |
| `types/api/system/dict.ts` | `vo/systemv2/dict.py` | `dto/systemv2/dict.py` |
| `types/api/system/function.ts` | `vo/systemv2/function.py` | `dto/systemv2/function.py` |
| `types/api/system/log.ts` | `vo/systemv2/log.py` | `dto/systemv2/log.py` |
| `types/api/system/asyncTask.ts` | `vo/systemv2/async_task.py` | `dto/systemv2/async_task.py` |
| `types/api/system/upload.ts` | `vo/systemv2/upload.py` | `dto/systemv2/upload.py` |
| `types/api/system/adminDashboard.ts` | `vo/systemv2/admin_dashboard.py` | — |
| `types/api/education/course.ts` | `vo/educationv2/course.py` | `dto/educationv2/course.py` |
| `types/api/education/student.ts` | `vo/educationv2/student.py` | `dto/educationv2/student.py` |
| `types/api/education/teacher.ts` | `vo/educationv2/teacher.py` | `dto/educationv2/teacher.py` |
| `types/api/education/chapter.ts` | `vo/educationv2/chapter.py` | `dto/educationv2/chapter.py` |
| `types/api/education/chapterResource.ts` | `vo/educationv2/chapter_resource.py` | `dto/educationv2/chapter_resource.py` |
| `types/api/education/knowledgeGraph.ts` | `vo/educationv2/knowledge_graph.py` | `dto/educationv2/knowledge_graph.py` |
| `types/api/education/stats.ts` | `vo/educationv2/stats.py` | `dto/educationv2/stats.py` |
| `types/api/education/agent.ts` | `vo/educationv2/agent.py` | `dto/educationv2/agent.py` |
| `types/api/education/courseExercise.ts` | `vo/educationv2/course_exercise.py` | `dto/educationv2/course_exercise.py` |
| `types/api/common/auth.ts` | `vo/commonv2/auth.py` | `dto/commonv2/auth.py` |
| `types/api/common/captcha.ts` | `vo/commonv2/captcha.py` | `dto/commonv2/captcha.py` |
| `types/api/tool/job.ts` | `vo/toolv2/job.py` | `dto/toolv2/job.py` |
| `types/api/tool/gen.ts` | `vo/toolv2/gen.py` | `dto/toolv2/gen.py` |

All backend paths are relative to `graphedu/common/models/`.

## Quick Fix Templates

### Adding a missing field

```typescript
// In types/api/{module}/{entity}.ts
export interface XxxVO {
  /** field description (from backend Field(description=...)) */
  fieldName: string      // required field
  anotherField?: number  // optional field (backend: T | None)
}
```

### Fixing an import path

```typescript
// Wrong
import type { UserDetailVO } from '@/types/api/user'
// Correct
import type { UserDetailVO } from '@/types/api/system/user'
```

### Fixing API return type

```typescript
// List endpoint (paginated)
function getXxxList(params: XxxQueryDTO): Promise<ResponseType<PageResponse<XxxListVO>>>

// Detail endpoint
function getXxxDetail(id: number): Promise<ResponseType<XxxDetailVO>>

// Create/Update (no data)
function addXxx(data: XxxCreateDTO): Promise<ResponseType<null>>
```
