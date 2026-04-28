import * as echarts from 'echarts/core'

import { BarChart, HeatmapChart } from 'echarts/charts'
import { TooltipComponent, GridComponent, VisualMapComponent, CalendarComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

import type {
  // 系列类型的定义后缀都为 SeriesOption
  BarSeriesOption,
  HeatmapSeriesOption,
} from 'echarts/charts'
import type {
  // 组件类型的定义后缀都为 ComponentOption
  TooltipComponentOption,
  GridComponentOption,
  VisualMapComponentOption,
  CalendarComponentOption,
} from 'echarts/components'
import type { ComposeOption } from 'echarts/core'

// 通过 ComposeOption 来组合出一个只有必须组件和图表的 Option 类型
type ECOption = ComposeOption<
  | BarSeriesOption
  | HeatmapSeriesOption
  | TooltipComponentOption
  | GridComponentOption
  | VisualMapComponentOption
  | CalendarComponentOption
>

// 注册必须的组件
echarts.use([
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
  CalendarComponent,

  BarChart,
  HeatmapChart,

  CanvasRenderer,
])

export { echarts, type ECOption }
