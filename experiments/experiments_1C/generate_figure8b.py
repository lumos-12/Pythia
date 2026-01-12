import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 设置样式
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 13,
    'legend.fontsize': 11,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'figure.titlesize': 15
})

# 读取数据
df = pd.read_csv('figure8b.csv')

# 分析数据中的benchmark
benchmarks = df['Trace'].unique()

# 定义DRAM带宽配置
dram_bandwidths = [150, 300, 600, 1200, 4800, 9600]
# 创建均匀分布的x轴位置
x_positions = np.arange(len(dram_bandwidths))

bandwidth_suffixes = ['', '_MTPS150', '_MTPS300', '_MTPS600', '_MTPS1200', '_MTPS4800', '_MTPS9600']

# 定义预取器
prefetchers = ['spp', 'bingo', 'mlop', 'pythia']
prefetcher_labels = ['SPP', 'Bingo', 'MLOP', 'Pythia']
prefetcher_colors = {
    'SPP': '#1f77b4',    # 蓝色
    'Bingo': '#2ca02c',  # 绿色
    'MLOP': '#9467bd',   # 紫色
    'Pythia': '#d62728'  # 红色
}

# ==================== 计算几何平均 IPC 比率 ====================
def calculate_geomean(values):
    """计算几何平均值"""
    if len(values) == 0:
        return 0
    
    # 计算几何平均：exp(mean(log(values)))
    log_values = np.log(values)
    geomean = np.exp(np.mean(log_values))
    return geomean

# 存储每个带宽和预取器的IPC比率
geomean_results = {pref_label: {} for pref_label in prefetcher_labels}
detailed_results = {pref_label: {} for pref_label in prefetcher_labels}

# 为每个DRAM带宽配置计算
for bw_idx, bandwidth in enumerate(dram_bandwidths):
    suffix = bandwidth_suffixes[bw_idx + 1] if bandwidth != 9600 else '_MTPS9600'
    
    for pref_idx, (pref_key, pref_label) in enumerate(zip(prefetchers, prefetcher_labels)):
        ipc_ratios = []
        detailed_ratios = []
        
        # 为每个benchmark计算IPC比率
        for bench in benchmarks:
            # 获取baseline数据
            baseline_exp = 'nopref' + (suffix if suffix != '' else '')
            baseline_data = df[(df['Trace'] == bench) & (df['Exp'] == baseline_exp)]
            
            # 获取预取器数据
            prefetcher_exp = pref_key + (suffix if suffix != '' else '')
            prefetcher_data = df[(df['Trace'] == bench) & (df['Exp'] == prefetcher_exp)]
            
            if not baseline_data.empty and not prefetcher_data.empty:
                baseline_ipc = baseline_data.iloc[0]['Core_0_IPC']
                prefetcher_ipc = prefetcher_data.iloc[0]['Core_0_IPC']
                
                # 计算IPC比率
                ipc_ratio = prefetcher_ipc / baseline_ipc
                ipc_ratios.append(ipc_ratio)
                detailed_ratios.append({
                    'benchmark': bench,
                    'baseline_ipc': baseline_ipc,
                    'prefetcher_ipc': prefetcher_ipc,
                    'ipc_ratio': ipc_ratio
                })
        
        # 计算几何平均
        if ipc_ratios:
            geomean_ratio = calculate_geomean(ipc_ratios)
            # 使用x轴位置作为键，而不是带宽值
            geomean_results[pref_label][bw_idx] = geomean_ratio
            detailed_results[pref_label][bw_idx] = detailed_ratios

# ==================== 创建图形 ====================
fig, ax = plt.subplots(figsize=(12, 8))

# 设置线条样式
line_styles = {
    'SPP': '-',
    'Bingo': '--',
    'MLOP': '-.',
    'Pythia': ':'
}

markers = {
    'SPP': 'o',
    'Bingo': 's',
    'MLOP': '^',
    'Pythia': 'D'
}

# 为每个预取器绘制折线图
for pref_label in prefetcher_labels:
    if geomean_results[pref_label]:
        # 提取数据点（按x_positions顺序）
        x_points = sorted(geomean_results[pref_label].keys())
        ratios = [geomean_results[pref_label][x] for x in x_points]
        
        # 绘制折线图（不添加数值标签）
        ax.plot(x_points, ratios,
                color=prefetcher_colors[pref_label],
                linestyle=line_styles[pref_label],
                linewidth=2.5,
                marker=markers[pref_label],
                markersize=8,
                markerfacecolor='white',
                markeredgecolor=prefetcher_colors[pref_label],
                markeredgewidth=2,
                label=pref_label)

# 设置图形属性
ax.set_xlabel('DRAM Million Transfers per Second (MTPS)', fontsize=13)
ax.set_ylabel('Geomean Speedup over No Prefetching\n(IPC_prefetcher / IPC_baseline)', fontsize=13)
ax.set_title('Figure 8(b): Performance vs DRAM Bandwidth', 
             fontsize=15, fontweight='bold', pad=15)

# 设置x轴刻度（均匀分布，显示实际带宽值）
ax.set_xticks(x_positions)
ax.set_xticklabels([str(bw) for bw in dram_bandwidths], fontsize=12)

# 添加网格
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)

# 添加基线参考线（比值为1.0）
ax.axhline(y=1.0, color='black', linestyle='-', linewidth=1.5, alpha=0.5,
           label='Baseline (Ratio = 1.0)')

# 设置y轴范围
all_ratios = []
for pref_label in prefetcher_labels:
    if geomean_results[pref_label]:
        all_ratios.extend(geomean_results[pref_label].values())

if all_ratios:
    min_ratio = min(all_ratios)
    max_ratio = max(all_ratios)
    
    # 为标签留出空间
    y_min = min(min_ratio * 0.95, 0.8)  # 至少显示0.8
    y_max = max_ratio * 1.08
    
    ax.set_ylim(y_min, y_max)
    # 设置均匀的y轴刻度
    y_ticks = np.arange(0.8, max_ratio * 1.05, 0.1)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f'{y:.1f}' for y in y_ticks], fontsize=12)

# 添加图例
ax.legend(loc='best', fontsize=11, frameon=True, ncol=2)

# 调整布局
plt.tight_layout()

# 保存图形
plt.savefig('figure8b_dram_bandwidth_performance.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
plt.savefig('figure8b_dram_bandwidth_performance.pdf', bbox_inches='tight', pad_inches=0.1)

# 显示图形
plt.show()

# ==================== 打印详细数据 ====================
print("\n" + "="*80)
print("DETAILED ANALYSIS FOR FIGURE 8(b)")
print("="*80)

print("\n1. GEOMEAN SPEEDUP BY DRAM BANDWIDTH:")
print("-"*70)
header = f"{'Bandwidth':<12} " + " ".join([f"{pref_label:<10}" for pref_label in prefetcher_labels])
print(header)
print("-"*70)

for i, bandwidth in enumerate(dram_bandwidths):
    row = f"{bandwidth:<12}"
    for pref_label in prefetcher_labels:
        if i in geomean_results[pref_label]:
            ratio = geomean_results[pref_label][i]
            row += f"{ratio:<10.3f}"
        else:
            row += f"{'N/A':<10}"
    print(row)

print("\n2. PERFORMANCE IMPROVEMENT BY BANDWIDTH (%):")
print("-"*70)
header = f"{'Bandwidth':<12} " + " ".join([f"{pref_label:<10}" for pref_label in prefetcher_labels])
print(header)
print("-"*70)

for i, bandwidth in enumerate(dram_bandwidths):
    row = f"{bandwidth:<12}"
    for pref_label in prefetcher_labels:
        if i in geomean_results[pref_label]:
            ratio = geomean_results[pref_label][i]
            improvement = (ratio - 1.0) * 100
            row += f"{improvement:<+10.1f}%"
        else:
            row += f"{'N/A':<10}"
    print(row)

print("\n3. PERFORMANCE TRENDS ANALYSIS:")
print("-"*50)

# 分析性能趋势
for pref_label in prefetcher_labels:
    if geomean_results[pref_label]:
        # 按x_positions顺序获取数据
        x_points = sorted(geomean_results[pref_label].keys())
        ratios = [geomean_results[pref_label][x] for x in x_points]
        bandwidths = [dram_bandwidths[x] for x in x_points]
        
        print(f"\n{pref_label}:")
        
        # 计算低带宽和高带宽的性能
        low_bw = bandwidths[0]
        high_bw = bandwidths[-1]
        low_perf = ratios[0]
        high_perf = ratios[-1]
        
        print(f"  Performance at {low_bw} MTPS: {low_perf:.3f} ({(low_perf-1)*100:+.1f}%)")
        print(f"  Performance at {high_bw} MTPS: {high_perf:.3f} ({(high_perf-1)*100:+.1f}%)")
        print(f"  Improvement from low to high bandwidth: {((high_perf/low_perf)-1)*100:+.1f}%")
        
        # 计算带宽敏感性
        if len(bandwidths) >= 2:
            perf_delta = ratios[-1] - ratios[0]
            bw_delta = bandwidths[-1] / bandwidths[0]
            sensitivity = perf_delta / np.log10(bw_delta)
            print(f"  Bandwidth sensitivity: {sensitivity:.3f} (higher = more sensitive)")

print("\n4. BANDWIDTH CONSTRAINED PERFORMANCE RANKING:")
print("-"*50)

# 在不同带宽下对预取器进行排名
for i, bandwidth in enumerate(dram_bandwidths):
    # 检查所有预取器在该带宽下是否有数据
    has_all_data = all(i in geomean_results[pref_label] for pref_label in prefetcher_labels)
    
    if has_all_data:
        ranking = sorted([(pref_label, geomean_results[pref_label][i]) 
                         for pref_label in prefetcher_labels], 
                        key=lambda x: x[1], reverse=True)
        
        print(f"\n{bandwidth} MTPS Ranking:")
        for rank, (pref_label, ratio) in enumerate(ranking, 1):
            improvement = (ratio - 1.0) * 100
            print(f"  {rank}. {pref_label}: {ratio:.3f} ({improvement:+.1f}%)")

print("\n5. BEST PREFETCHER AT EACH BANDWIDTH LEVEL:")
print("-"*50)

best_at_each_bw = {}
for i, bandwidth in enumerate(dram_bandwidths):
    best_pref = None
    best_ratio = 0
    
    for pref_label in prefetcher_labels:
        if i in geomean_results[pref_label]:
            ratio = geomean_results[pref_label][i]
            if ratio > best_ratio:
                best_ratio = ratio
                best_pref = pref_label
    
    if best_pref:
        best_at_each_bw[bandwidth] = (best_pref, best_ratio)
        print(f"{bandwidth} MTPS: {best_pref} ({best_ratio:.3f}, {(best_ratio-1)*100:+.1f}%)")

print("\n6. INTERPRETATION:")
print("-"*50)
print("""
- Geomean Speedup: Geometric mean of IPC_prefetcher / IPC_baseline across all benchmarks
- Ratio > 1.0: Performance improvement over no prefetching baseline
- Ratio < 1.0: Performance degradation compared to baseline
- Lower bandwidth (150-600 MTPS): Represents memory-constrained scenarios
- Higher bandwidth (1200-9600 MTPS): Represents memory-abundant scenarios
- X-axis is uniformly spaced for better visualization
- Good prefetchers maintain high performance across all bandwidth levels
- Some prefetchers may perform well at high bandwidth but poorly at low bandwidth
""")

# ==================== 创建附加图形：性能提升百分比（不显示数值标签） ====================
print("\n7. ADDITIONAL VISUALIZATION: Percentage Performance Improvement (no labels)")
print("-"*50)

fig2, ax2 = plt.subplots(figsize=(12, 8))

# 为每个预取器绘制百分比提升折线图（不显示数值标签）
for pref_label in prefetcher_labels:
    if geomean_results[pref_label]:
        x_points = sorted(geomean_results[pref_label].keys())
        percentages = [(geomean_results[pref_label][x] - 1.0) * 100 for x in x_points]
        
        # 绘制折线图（不添加数值标签）
        ax2.plot(x_points, percentages,
                color=prefetcher_colors[pref_label],
                linestyle=line_styles[pref_label],
                linewidth=2.5,
                marker=markers[pref_label],
                markersize=8,
                markerfacecolor='white',
                markeredgecolor=prefetcher_colors[pref_label],
                markeredgewidth=2,
                label=pref_label)

# 设置图形属性
ax2.set_xlabel('DRAM Million Transfers per Second (MTPS)', fontsize=13)
ax2.set_ylabel('Performance Improvement (%)', fontsize=13)
ax2.set_title('Percentage Performance Improvement vs DRAM Bandwidth', 
              fontsize=15, fontweight='bold', pad=15)

# 设置x轴刻度（均匀分布，显示实际带宽值）
ax2.set_xticks(x_positions)
ax2.set_xticklabels([str(bw) for bw in dram_bandwidths], fontsize=12)

# 添加网格
ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)

# 添加零线
ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.5)

# 设置y轴范围
all_percentages = []
for pref_label in prefetcher_labels:
    if geomean_results[pref_label]:
        x_points = sorted(geomean_results[pref_label].keys())
        percentages = [(geomean_results[pref_label][x] - 1.0) * 100 for x in x_points]
        all_percentages.extend(percentages)

if all_percentages:
    min_percent = min(all_percentages)
    max_percent = max(all_percentages)
    
    # 为标签留出空间
    y_margin = max(abs(min_percent), abs(max_percent)) * 0.15
    ax2.set_ylim(min_percent - y_margin, max_percent + y_margin)

# 添加图例
ax2.legend(loc='best', fontsize=11, frameon=True, ncol=2)

# 调整布局
plt.tight_layout()
plt.savefig('figure8b_percentage_improvement.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
print("Additional visualization saved as 'figure8b_percentage_improvement.png'")
