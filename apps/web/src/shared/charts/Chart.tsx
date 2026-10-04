import * as echarts from "echarts/core";
import { LineChart, BarChart } from "echarts/charts";
import { GridComponent, TooltipComponent, MarkLineComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import { useEffect, useRef } from "react";
import type { EChartsOption } from "echarts";
echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, MarkLineComponent, SVGRenderer]);
export function Chart({ option, label }: { option: EChartsOption; label: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current, undefined, { renderer: "svg" });
    chartRef.current = chart;
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(ref.current);
    return () => { observer.disconnect(); chartRef.current = null; chart.dispose(); };
  }, []);
  useEffect(() => { chartRef.current?.setOption(option, true); }, [option]);
  return <div ref={ref} className="chart" role="img" aria-label={label}/>;
}
