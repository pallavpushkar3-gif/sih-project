import * as echarts from "echarts";
import {useEffect,useRef} from "react";
import type {EChartsOption} from "echarts";
export function Chart({option,label}:{option:EChartsOption;label:string}){const ref=useRef<HTMLDivElement>(null);useEffect(()=>{if(!ref.current)return;const chart=echarts.init(ref.current);chart.setOption(option);const resize=()=>chart.resize();window.addEventListener("resize",resize);return()=>{window.removeEventListener("resize",resize);chart.dispose()}},[option]);return <div ref={ref} className="chart" role="img" aria-label={label}/>}
