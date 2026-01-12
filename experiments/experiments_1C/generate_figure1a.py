import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# 设置样式
plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'legend.fontsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 13
})

# 读取数据
df = pd.read_csv('figure1.csv')

# 提取benchmark名称
df['Benchmark'] = df['Trace'].apply(lambda x: x.split('-')[0])

# 分析每个benchmark的数据
benchmarks = df['Benchmark'].unique()
prefetchers = ['nopref', 'spp', 'bingo', 'mlop', 'pythia']

# 为每个benchmark计算指标
results = {}

for bench in benchmarks:
    bench_data = df[df['Benchmark'] == bench]
    results[bench] = {}
    
    for pref in prefetchers:
        if pref in bench_data['Exp'].values:
            data = bench_data[bench_data['Exp'] == pref].iloc[0]
            results[bench][pref] = {
                'IPC': data['Core_0_IPC'],
                'LLC_load_miss': data['Core_0_LLC_load_miss'],
                'LLC_RFO_miss': data['Core_0_LLC_RFO_miss'],
                'LLC_prefetch_miss': data['Core_0_LLC_prefetch_miss'],
                'LLC_total_miss': data['Core_0_LLC_total_miss'],
                'LLC_prefetch_hit': data['Core_0_LLC_prefetch_hit']
            }

# ==================== 计算相关指标 ====================
# 定义颜色（调整堆叠顺序）
colors = {
    'coverage': '#4CAF50',      # 绿色 - 覆盖率（底部）
    'uncovered': '#FFA726',     # 橙色 - 未覆盖率（中间）
    'overprediction': '#EF5350' # 红色 - 过度预测率（顶部）
}

# 定义预取器配置
prefetchers_to_plot = ['spp', 'bingo', 'pythia']
prefetcher_labels = ['SPP', 'Bingo', 'Pythia']
prefetcher_colors = ['#1f77b4', '#2ca02c', '#d62728']  # 蓝、绿、红

# 计算LLC read misses
def calculate_read_misses(data):
    """计算LLC read misses = LLC_load_miss + LLC_RFO_miss + LLC_prefetch_miss"""
    return (data['LLC_load_miss'] + 
            data['LLC_RFO_miss'] + 
            data['LLC_prefetch_miss'])

# 计算覆盖率、未覆盖率、过度预测率
def calculate_miss_fractions(baseline_data, prefetcher_data):
    """
    计算相对于baseline的各个分数
    Coverage = (baseline_LLC_load_miss - prefetcher_LLC_load_miss) / baseline_LLC_load_miss
    Overprediction = (prefetcher_read_miss - baseline_read_miss) / baseline_read_miss
    Uncovered = 1 - Coverage
    """
    # 获取baseline数据
    baseline_load_miss = baseline_data['LLC_load_miss']
    baseline_read_miss = calculate_read_misses(baseline_data)
    
    # 获取预取器数据
    prefetcher_load_miss = prefetcher_data['LLC_load_miss']
    prefetcher_read_miss = calculate_read_misses(prefetcher_data)
    
    # 计算覆盖率
    if baseline_load_miss > 0:
        coverage = (baseline_load_miss - prefetcher_load_miss) / baseline_load_miss
        coverage = max(0, min(1, coverage))
    else:
        coverage = 0
    
    # 未覆盖率 = 1 - 覆盖率
    uncovered = 1 - coverage
    
    # 计算过度预测率
    if baseline_read_miss > 0:
        overprediction = (prefetcher_read_miss - baseline_read_miss) / baseline_read_miss
        overprediction = max(0, overprediction)
    else:
        overprediction = 0
    
    return coverage, uncovered, overprediction

# ==================== 重新组织数据 ====================
# 收集每个trace下所有预取器的数据
trace_data = {}

for bench in benchmarks:
    bench_name = 'sphinx3' if bench.startswith('482') else 'GemsFDTD'
    
    if bench in results and 'nopref' in results[bench]:
        baseline_data = results[bench]['nopref']
        trace_data[bench_name] = {}
        
        for pref, pref_label in zip(prefetchers_to_plot, prefetcher_labels):
            if pref in results[bench]:
                prefetcher_data = results[bench][pref]
                coverage, uncovered, overprediction = calculate_miss_fractions(
                    baseline_data, prefetcher_data
                )
                
                trace_data[bench_name][pref_label] = {
                    'coverage': coverage * 100,
                    'uncovered': uncovered * 100,
                    'overprediction': overprediction * 100,
                    'total': (coverage + uncovered + overprediction) * 100
                }

# ==================== 创建新图形 ====================
fig, ax = plt.subplots(figsize=(10, 7))

# 确定x轴位置
traces = list(trace_data.keys())
x = np.arange(len(traces))
group_width = 0.8  # 每组的总宽度
bar_width = group_width / len(prefetchers_to_plot)  # 每个柱子的宽度

# 为每个trace和预取器绘制堆叠柱状图
for i, trace in enumerate(traces):
    for j, (pref_label, color) in enumerate(zip(prefetcher_labels, prefetcher_colors)):
        if pref_label in trace_data[trace]:
            data = trace_data[trace][pref_label]
            
            # 计算x位置（中心对齐）
            x_pos = x[i] - group_width/2 + (j + 0.5) * bar_width
            
            # 按照新顺序绘制堆叠柱状图：
            # 1. 覆盖率（绿色）- 底部
            # 2. 未覆盖率（橙色）- 中间
            # 3. 过度预测率（红色）- 顶部
            
            # 绘制覆盖率（底部）
            ax.bar(x_pos, data['coverage'], bar_width * 0.9,
                  color=colors['coverage'], alpha=0.9,
                  edgecolor='black', linewidth=0.8,
                  label='Coverage' if i == 0 and j == 0 else "")
            
            # 绘制未覆盖率（中间，堆叠在覆盖率之上）
            ax.bar(x_pos, data['uncovered'], bar_width * 0.9,
                  bottom=data['coverage'],
                  color=colors['uncovered'], alpha=0.9,
                  edgecolor='black', linewidth=0.8,
                  label='Uncovered' if i == 0 and j == 0 else "")
            
            # 绘制过度预测率（顶部，堆叠在未覆盖率之上）
            ax.bar(x_pos, data['overprediction'], bar_width * 0.9,
                  bottom=data['coverage'] + data['uncovered'],
                  color=colors['overprediction'], alpha=0.9,
                  edgecolor='black', linewidth=0.8,
                  label='Overprediction' if i == 0 and j == 0 else "")
            
            # 在柱子顶部添加总计百分比
            total = data['total']
            ax.text(x_pos, total + 1.5, f'{total:.0f}%',
                   ha='center', va='bottom', fontsize=8, fontweight='bold')
            
            # 在柱子内部添加预取器标签
            ax.text(x_pos, -5, pref_label,
                   ha='center', va='top', fontsize=9, fontweight='bold',
                   color=color, rotation=0)

# 设置图形属性
ax.set_xlabel('Benchmark', fontsize=12)
ax.set_ylabel('Fraction of Baseline LLC Misses (%)', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(traces, fontsize=11)
ax.set_title('Figure 1(a): Prefetcher Coverage and Overprediction Analysis', 
             fontsize=14, fontweight='bold', pad=15)

# 添加网格
ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.5)

# 设置y轴范围
all_totals = []
for trace in traces:
    for pref_label in prefetcher_labels:
        if pref_label in trace_data[trace]:
            all_totals.append(trace_data[trace][pref_label]['total'])

if all_totals:
    max_total = max(all_totals)
    ax.set_ylim(0, max_total * 1.15)

# 添加堆叠部分的图例
stacked_legend_elements = [
    mpatches.Patch(facecolor=colors['coverage'], edgecolor='black', linewidth=0.8,
                   label='Coverage', alpha=0.9),
    mpatches.Patch(facecolor=colors['uncovered'], edgecolor='black', linewidth=0.8,
                   label='Uncovered', alpha=0.9),
    mpatches.Patch(facecolor=colors['overprediction'], edgecolor='black', linewidth=0.8,
                   label='Overprediction', alpha=0.9)
]

# 添加预取器颜色的图例
prefetcher_legend_elements = [
    plt.Line2D([0], [0], color=prefetcher_colors[i], linewidth=3, label=pref_label)
    for i, pref_label in enumerate(prefetcher_labels)
]

# 创建复合图例
all_legend_elements = stacked_legend_elements + prefetcher_legend_elements
ax.legend(handles=all_legend_elements, loc='upper left', 
          bbox_to_anchor=(1.02, 1), fontsize=10, frameon=True,
          title="Legend", title_fontsize=11)

# 调整布局
plt.tight_layout(rect=[0, 0, 0.85, 1])  # 为图例留出空间

# 保存图形
plt.savefig('figure1a_grouped_stacked.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
plt.savefig('figure1a_grouped_stacked.pdf', bbox_inches='tight', pad_inches=0.1)

# 显示图形
plt.show()

# ==================== 打印详细数据 ====================
print("\n" + "="*80)
print("DETAILED ANALYSIS FOR FIGURE 1(a) - GROUPED VIEW")
print("="*80)

print("\n1. DATA BY TRACE:")
print("-"*90)

for trace in traces:
    print(f"\n{trace}:")
    print("-" * 40)
    print(f"{'Prefetcher':<8} {'Coverage':<10} {'Uncovered':<10} {'Overpred':<10} {'Total':<10}")
    print("-" * 40)
    
    for pref_label in prefetcher_labels:
        if pref_label in trace_data[trace]:
            data = trace_data[trace][pref_label]
            print(f"{pref_label:<8} {data['coverage']:<10.1f} {data['uncovered']:<10.1f} "
                  f"{data['overprediction']:<10.1f} {data['total']:<10.1f}")

print("\n2. SUMMARY STATISTICS BY PREFETCHER:")
print("-"*60)

summary_by_prefetcher = {pref: {'coverage': [], 'uncovered': [], 'overpred': [], 'total': []} 
                         for pref in prefetcher_labels}

for trace in traces:
    for pref_label in prefetcher_labels:
        if pref_label in trace_data[trace]:
            data = trace_data[trace][pref_label]
            summary_by_prefetcher[pref_label]['coverage'].append(data['coverage'])
            summary_by_prefetcher[pref_label]['uncovered'].append(data['uncovered'])
            summary_by_prefetcher[pref_label]['overpred'].append(data['overprediction'])
            summary_by_prefetcher[pref_label]['total'].append(data['total'])

for pref_label in prefetcher_labels:
    if summary_by_prefetcher[pref_label]['coverage']:
        avg_coverage = np.mean(summary_by_prefetcher[pref_label]['coverage'])
        avg_uncovered = np.mean(summary_by_prefetcher[pref_label]['uncovered'])
        avg_overpred = np.mean(summary_by_prefetcher[pref_label]['overpred'])
        avg_total = np.mean(summary_by_prefetcher[pref_label]['total'])
        
        print(f"\n{pref_label}:")
        print(f"  Average Coverage: {avg_coverage:.1f}%")
        print(f"  Average Uncovered: {avg_uncovered:.1f}%")
        print(f"  Average Overprediction: {avg_overpred:.1f}%")
        print(f"  Average Total: {avg_total:.1f}%")
        print(f"  Uncovered+Coverage: {(avg_uncovered + avg_coverage):.1f}% (should be 100%)")

print("\n3. COMPARISON TABLE:")
print("-"*70)
print(f"{'Benchmark':<10} {'Metric':<12} {'SPP':<10} {'Bingo':<10} {'Pythia':<10}")
print("-"*70)

metrics = ['Coverage', 'Uncovered', 'Overprediction', 'Total']
for trace in traces:
    for metric in metrics:
        metric_key = metric.lower()
        row = [f"{trace}", f"{metric}"]
        for pref_label in prefetcher_labels:
            if pref_label in trace_data[trace]:
                value = trace_data[trace][pref_label][metric_key]
                row.append(f"{value:.1f}%")
            else:
                row.append("N/A")
        print(f"{row[0]:<10} {row[1]:<12} {row[2]:<10} {row[3]:<10} {row[4]:<10}")

# ==================== 创建详细数据表格 ====================
print("\n4. DETAILED DATA TABLE:")
print("-"*120)

detailed_data = []
for trace in traces:
    for pref_label in prefetcher_labels:
        if pref_label in trace_data[trace]:
            data = trace_data[trace][pref_label]
            detailed_data.append({
                'Benchmark': trace,
                'Prefetcher': pref_label,
                'Coverage_%': data['coverage'],
                'Uncovered_%': data['uncovered'],
                'Overprediction_%': data['overprediction'],
                'Total_%': data['total'],
                'Coverage+Uncovered': data['coverage'] + data['uncovered']
            })

detailed_df = pd.DataFrame(detailed_data)
print(detailed_df.to_string(index=False, float_format=lambda x: f'{x:.1f}'))

# ==================== 性能对比分析 ====================
print("\n5. PERFORMANCE COMPARISON:")
print("-"*50)

for trace in traces:
    print(f"\n{trace}:")
    # 找出覆盖率最高的预取器
    best_coverage = 0
    best_prefetcher = None
    
    for pref_label in prefetcher_labels:
        if pref_label in trace_data[trace]:
            coverage = trace_data[trace][pref_label]['coverage']
            if coverage > best_coverage:
                best_coverage = coverage
                best_prefetcher = pref_label
    
    if best_prefetcher:
        print(f"  Highest Coverage: {best_prefetcher} ({best_coverage:.1f}%)")
        
        # 找出过度预测率最低的预取器
        best_overpred = float('inf')
        best_prefetcher_low_overpred = None
        
        for pref_label in prefetcher_labels:
            if pref_label in trace_data[trace]:
                overpred = trace_data[trace][pref_label]['overprediction']
                if overpred < best_overpred:
                    best_overpred = overpred
                    best_prefetcher_low_overpred = pref_label
        
        if best_prefetcher_low_overpred:
            print(f"  Lowest Overprediction: {best_prefetcher_low_overpred} ({best_overpred:.1f}%)")
            
            # 计算效率（覆盖率/总预取率）
            efficiency_data = {}
            for pref_label in prefetcher_labels:
                if pref_label in trace_data[trace]:
                    data = trace_data[trace][pref_label]
                    if data['total'] > 0:
                        efficiency = data['coverage'] / data['total'] * 100
                        efficiency_data[pref_label] = efficiency
            
            if efficiency_data:
                best_efficiency = max(efficiency_data.values())
                best_prefetcher_eff = max(efficiency_data, key=efficiency_data.get)
                print(f"  Highest Efficiency: {best_prefetcher_eff} ({best_efficiency:.1f}%)")
