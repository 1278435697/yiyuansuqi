/**
 * EchartTimeSim —— 时空推演模拟器图表（小倍数多图表）
 *
 * 七项指标（版型/衣长/袖宽/色彩/纹样/面料/礼制）各一张趋势小图：
 * 实线=参数推演结果，虚线=史实基线。
 */
import * as echarts from "echarts";
import { fetchSimulatorTrend } from "@/api/modules";

export interface TrendData {
  eras: { name: string; year: string; short: string }[];
  metrics: Record<string, string>;
  series: Record<string, { name: string; forecast: number[]; baseline: number[] }>;
}

export class EchartTimeSim {
  private containers: HTMLDivElement[];
  private charts: echarts.ECharts[] = [];
  private data: TrendData | null = null;

  constructor(containers: HTMLDivElement[]) {
    this.containers = containers;
  }

  public async load(params: Record<string, number>) {
    this.data = (await fetchSimulatorTrend(params)) as unknown as TrendData;
    this.render();
  }

  public render() {
    if (!this.data) return;
    const keys = Object.keys(this.data.series);
    const palette = ["#7e2418", "#b98a2f", "#2f6b5e", "#5b5144", "#8c806e", "#a93226", "#6b4e2d"];
    keys.forEach((key, idx) => {
      if (!this.containers[idx]) return;
      const s = this.data!.series[key];
      const chart = this.charts[idx] ?? echarts.init(this.containers[idx]);
      this.charts[idx] = chart;
      chart.setOption({
        grid: { left: 34, right: 8, top: 22, bottom: 26 },
        tooltip: { trigger: "axis", confine: true },
        legend: { show: false },
        title: {
          text: s.name,
          left: 6,
          top: 0,
          textStyle: { fontSize: 12, color: "#5b5144", fontWeight: 700 },
        },
        xAxis: {
          type: "category",
          data: this.data!.eras.map((e) => e.short),
          axisLine: { lineStyle: { color: "#d8c9a8" } },
          axisLabel: { fontSize: 10, color: "#8c806e" },
          axisTick: { show: false },
        },
        yAxis: {
          type: "value",
          min: 0,
          max: 100,
          splitLine: { lineStyle: { color: "#eee5d2" } },
          axisLabel: { fontSize: 10, color: "#8c806e" },
        },
        series: [
          {
            name: "推演",
            type: "line",
            data: s.forecast,
            smooth: true,
            symbol: "circle",
            symbolSize: 5,
            lineStyle: { width: 2.5, color: palette[idx % palette.length] },
            itemStyle: { color: palette[idx % palette.length] },
          },
          {
            name: "史实基线",
            type: "line",
            data: s.baseline,
            smooth: true,
            symbol: "none",
            lineStyle: { width: 1.5, type: "dashed", color: "#b0a48c" },
          },
        ],
      });
    });
  }

  public dispose() {
    this.charts.forEach((c) => c.dispose());
    this.charts = [];
  }
}
