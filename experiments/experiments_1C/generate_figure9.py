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
df = pd.read_csv('figure7.csv')

# 分析每个benchmark的数据
benchmarks = df['Trace'].unique()
prefetchers = ['nopref', 'spp', 'bingo', 'mlop', 'pythia']
prefetcher_labels = ['SPP', 'Bingo', 'MLOP', 'Pythia']
prefetcher_keys = ['spp', 'bingo', 'mlop', 'pythia']

# 定义颜色（为每个预取器分配不同颜色）
colors = {
    'SPP': '#1f77b4',    # 蓝色
    'Bingo': '#2ca02c',  # 绿色
    'MLOP': '#9467bd',   # 紫色
    'Pythia': '#d62728'  # 红色
}

# ==================== 计算 IPC 比率 ====================
# 存储每个benchmark的baseline IPC
baseline_ipc = {}
for bench in benchmarks:
    bench_data = df[df['Trace'] == bench]
    if 'nopref' in bench_data['Exp'].values:
        baseline_data = bench_data[bench_data['Exp'] == 'nopref'].iloc[0]
        baseline_ipc[bench] = baseline_data['Core_0_IPC']

# 存储每个预取器的 IPC 比率（IPC_prefetcher / IPC_baseline）
prefetcher_ipc_ratios = {label: [] for label in prefetcher_labels}

# 计算每个benchmark和预取器的 IPC 比率
for bench in benchmarks:
    if bench in baseline_ipc:
        bench_data = df[df['Trace'] == bench]
        baseline = baseline_ipc[bench]
        
        for label, key in zip(prefetcher_labels, prefetcher_keys):
            if key in bench_data['Exp'].values:
                pref_data = bench_data[bench_data['Exp'] == key].iloc[0]
                pref_ipc = pref_data['Core_0_IPC']
                
                # 计算 IPC 比率：IPC_prefetcher / IPC_baseline
                ipc_ratio = pref_ipc / baseline
                prefetcher_ipc_ratios[label].append(ipc_ratio)

# 计算几何平均 IPC 比率
def calculate_geomean(values):
    """计算几何平均值"""
    if len(values) == 0:
        return 0
    
    # 计算几何平均：exp(mean(log(values)))
    log_values = np.log(values)
    geomean = np.exp(np.mean(log_values))
    return geomean

# 计算每个预取器的几何平均 IPC 比率
geomean_ipc_ratios = {}
for label in prefetcher_labels:
    if prefetcher_ipc_ratios[label]:
        geomean = calculate_geomean(prefetcher_ipc_ratios[label])
        geomean_ipc_ratios[label] = geomean

# 计算算术平均 IPC 比率
arithmetic_mean_ipc_ratios = {}
for label in prefetcher_labels:
    if prefetcher_ipc_ratios[label]:
        arithmetic_mean = np.mean(prefetcher_ipc_ratios[label])
        arithmetic_mean_ipc_ratios[label] = arithmetic_mean

# ==================== 创建图形（使用几何平均） ====================
fig, ax = plt.subplots(figsize=(10, 7))

# x轴位置
x = np.arange(len(prefetcher_labels))
width = 0.6

# 为每个预取器绘制柱状图（使用几何平均）
bars = []
for i, pref_label in enumerate(prefetcher_labels):
    if pref_label in geomean_ipc_ratios:
        ipc_ratio = geomean_ipc_ratios[pref_label]
        color = colors[pref_label]
        
        # 绘制柱状图
        bar = ax.bar(x[i], ipc_ratio, width,
                    color=color, alpha=0.8,
                    edgecolor='black', linewidth=1.5)
        bars.append(bar)
        
        # 在柱子顶部添加数值标签
        ax.text(x[i], ipc_ratio + 0.02, f'{ipc_ratio:.3f}',
               ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 在柱子内部添加预取器名称
        ax.text(x[i], ipc_ratio/2, pref_label,
               ha='center', va='center', fontsize=12, fontweight='bold',
               color='white')

# 设置图形属性
ax.set_xlabel('Prefetcher', fontsize=13)
ax.set_ylabel('Geomean IPC Ratio (IPC_prefetcher / IPC_baseline)', fontsize=13)
ax.set_xticks(x)
ax.set_xticklabels(prefetcher_labels, fontsize=12)
ax.set_title('Figure 8(a): Geometric Mean IPC Ratio of Prefetchers', 
             fontsize=15, fontweight='bold', pad=15)

# 添加网格
ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.8)

# 添加基线参考线（比值为1.0）
ax.axhline(y=1.0, color='black', linestyle='--', linewidth=1.5, alpha=0.7,
           label='Baseline (Ratio = 1.0)')

# 设置y轴范围
ratio_values = list(geomean_ipc_ratios.values())
if ratio_values:
    min_ratio = min(ratio_values)
    max_ratio = max(ratio_values)
    
    # 为标签留出空间
    y_min = min(min_ratio * 0.95, 0.8)  # 至少显示0.8
    y_max = max_ratio * 1.05
    
    ax.set_ylim(y_min, y_max)

# 添加图例
ax.legend(loc='upper left', fontsize=11, frameon=True)

# 调整布局
plt.tight_layout()

# 保存图形
plt.savefig('figure9a_geomean_ipc_ratio.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
plt.savefig('figure9a_geomean_ipc_ratio.pdf', bbox_inches='tight', pad_inches=0.1)

# 显示图形
plt.show()

# ==================== 打印详细数据 ====================
print("\n" + "="*80)
print("DETAILED ANALYSIS FOR FIGURE 8(a)")
print("="*80)

print("\n1. GEOMETRIC MEAN IPC RATIO BY PREFETCHER:")
print("-"*50)
print(f"{'Prefetcher':<8} {'Geomean Ratio':<15} {'Arithmetic Mean':<15} {'# of Benchmarks':<15}")
print("-"*50)

for pref_label in prefetcher_labels:
    if pref_label in geomean_ipc_ratios:
        geomean = geomean_ipc_ratios[pref_label]
        arithmetic = arithmetic_mean_ipc_ratios.get(pref_label, 0)
        num_benchmarks = len(prefetcher_ipc_ratios[pref_label])
        print(f"{pref_label:<8} {geomean:<15.3f} {arithmetic:<15.3f} {num_benchmarks:<15}")

print("\n2. DETAILED IPC RATIOS FOR EACH BENCHMARK:")
print("-"*100)

# 创建详细数据表格
detailed_data = []
for bench in benchmarks:
    if bench in baseline_ipc:
        bench_data = df[df['Trace'] == bench]
        baseline = baseline_ipc[bench]
        
        for label, key in zip(prefetcher_labels, prefetcher_keys):
            if key in bench_data['Exp'].values:
                pref_data = bench_data[bench_data['Exp'] == key].iloc[0]
                pref_ipc = pref_data['Core_0_IPC']
                ipc_ratio = pref_ipc / baseline
                
                detailed_data.append({
                    'Benchmark': bench,
                    'Prefetcher': label,
                    'Baseline_IPC': baseline,
                    'Prefetcher_IPC': pref_ipc,
                    'IPC_Ratio': ipc_ratio
                })

detailed_df = pd.DataFrame(detailed_data)
print(detailed_df.to_string(index=False, float_format=lambda x: f'{x:.3f}' if isinstance(x, float) else str(x)))

print("\n3. STATISTICAL SUMMARY:")
print("-"*50)

# 计算每个预取器的统计数据
for pref_label in prefetcher_labels:
    if prefetcher_ipc_ratios[pref_label]:
        ratios = prefetcher_ipc_ratios[pref_label]
        
        print(f"\n{pref_label}:")
        print(f"  Geometric Mean: {geomean_ipc_ratios.get(pref_label, 0):.3f}")
        print(f"  Arithmetic Mean: {np.mean(ratios):.3f}")
        print(f"  Standard Deviation: {np.std(ratios):.3f}")
        print(f"  Range: {min(ratios):.3f} to {max(ratios):.3f}")
        print(f"  Median: {np.median(ratios):.3f}")
        
        # 计算性能提升/降低的比例
        improved_count = sum(1 for r in ratios if r > 1.0)
        degraded_count = sum(1 for r in ratios if r < 1.0)
        same_count = sum(1 for r in ratios if r == 1.0)
        total_count = len(ratios)
        
        print(f"  Improved (Ratio > 1.0): {improved_count}/{total_count} ({improved_count/total_count*100:.1f}%)")
        print(f"  Degraded (Ratio < 1.0): {degraded_count}/{total_count} ({degraded_count/total_count*100:.1f}%)")
        if same_count > 0:
            print(f"  Same (Ratio = 1.0): {same_count}/{total_count} ({same_count/total_count*100:.1f}%)")
        
        # 计算平均性能提升百分比
        avg_percentage_improvement = (np.mean(ratios) - 1.0) * 100
        print(f"  Average Percentage Improvement: {avg_percentage_improvement:+.2f}%")

print("\n4. PERFORMANCE RANKING:")
print("-"*50)

# 按几何平均 IPC 比率排名
ranking_geomean = sorted([(pref, geomean_ipc_ratios[pref]) 
                         for pref in geomean_ipc_ratios.keys()], 
                        key=lambda x: x[1], reverse=True)

print("\nRanking by Geometric Mean IPC Ratio (highest to lowest):")
for rank, (pref, ratio) in enumerate(ranking_geomean, 1):
    print(f"  {rank}. {pref}: {ratio:.3f} ({(ratio-1.0)*100:+.1f}%)")

# 按算术平均 IPC 比率排名
ranking_arithmetic = sorted([(pref, arithmetic_mean_ipc_ratios[pref]) 
                            for pref in arithmetic_mean_ipc_ratios.keys()], 
                           key=lambda x: x[1], reverse=True)

print("\nRanking by Arithmetic Mean IPC Ratio (highest to lowest):")
for rank, (pref, ratio) in enumerate(ranking_arithmetic, 1):
    print(f"  {rank}. {pref}: {ratio:.3f} ({(ratio-1.0)*100:+.1f}%)")

print("\n5. COMPARISON WITH BASELINE AND BEST PREFETCHER:")
print("-"*50)

print("\nPerformance Comparison (IPC Ratio):")
best_pref = ranking_geomean[0][0] if ranking_geomean else None
for pref_label in prefetcher_labels:
    if pref_label in geomean_ipc_ratios:
        ratio = geomean_ipc_ratios[pref_label]
        percentage = (ratio - 1.0) * 100
        
        print(f"\n{pref_label}:")
        print(f"  IPC Ratio vs Baseline: {ratio:.3f}")
        print(f"  Percentage vs Baseline: {percentage:+.2f}%")
        
        if best_pref and pref_label != best_pref:
            best_ratio = geomean_ipc_ratios[best_pref]
            ratio_diff = ratio / best_ratio
            percentage_diff = (ratio - best_ratio) / best_ratio * 100
            print(f"  Ratio vs {best_pref}: {ratio_diff:.3f}")
            print(f"  Percentage vs {best_pref}: {percentage_diff:+.2f}%")

print("\n6. INTERPRETATION:")
print("-"*50)
print("""
- IPC Ratio: IPC_prefetcher / IPC_baseline
- Ratio > 1.0: Performance improvement over baseline
- Ratio < 1.0: Performance degradation compared to baseline
- Ratio = 1.0: Same performance as baseline
- Geometric mean is used to average ratios, as it better handles multiplicative data
- Higher ratios indicate better overall performance
""")

# ==================== 创建附加图形：算术平均与几何平均对比 ====================
print("\n7. ADDITIONAL VISUALIZATION: Geometric vs Arithmetic Mean Comparison")
print("-"*50)

fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

# 子图1：几何平均 IPC 比率
x_pos = np.arange(len(prefetcher_labels))
width = 0.35

for i, pref_label in enumerate(prefetcher_labels):
    if pref_label in geomean_ipc_ratios:
        # 几何平均
        geomean_val = geomean_ipc_ratios[pref_label]
        ax1.bar(x_pos[i] - width/2, geomean_val, width,
                color=colors[pref_label], alpha=0.7,
                edgecolor='black', linewidth=1.0,
                label='Geometric Mean' if i == 0 else "")
        
        # 算术平均
        arithmetic_val = arithmetic_mean_ipc_ratios.get(pref_label, 0)
        ax1.bar(x_pos[i] + width/2, arithmetic_val, width,
                color=colors[pref_label], alpha=0.4,
                edgecolor='black', linewidth=1.0,
                label='Arithmetic Mean' if i == 0 else "")
        
        # 添加数值标签
        ax1.text(x_pos[i] - width/2, geomean_val + 0.01, f'{geomean_val:.3f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax1.text(x_pos[i] + width/2, arithmetic_val + 0.01, f'{arithmetic_val:.3f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

ax1.set_xlabel('Prefetcher', fontsize=12)
ax1.set_ylabel('IPC Ratio', fontsize=12)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(prefetcher_labels, fontsize=11)
ax1.set_title('Geometric vs Arithmetic Mean IPC Ratio', fontsize=13, fontweight='bold')
ax1.axhline(y=1.0, color='black', linestyle='--', linewidth=1.5, alpha=0.5)
ax1.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.5)
ax1.legend(fontsize=10)

# 子图2：百分比性能提升
ax2.bar(x_pos, [(geomean_ipc_ratios.get(pref, 0)-1.0)*100 for pref in prefetcher_labels],
        width=0.6, color=[colors[pref] for pref in prefetcher_labels],
        alpha=0.8, edgecolor='black', linewidth=1.0)

# 添加数值标签
for i, pref_label in enumerate(prefetcher_labels):
    if pref_label in geomean_ipc_ratios:
        percentage = (geomean_ipc_ratios[pref_label] - 1.0) * 100
        ax2.text(i, percentage + (0.5 if percentage >= 0 else -1.0), 
                f'{percentage:+.1f}%',
                ha='center', va='bottom' if percentage >= 0 else 'top',
                fontsize=11, fontweight='bold')

ax2.set_xlabel('Prefetcher', fontsize=12)
ax2.set_ylabel('Performance Improvement (%)', fontsize=12)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(prefetcher_labels, fontsize=11)
ax2.set_title('Percentage Performance Improvement', fontsize=13, fontweight='bold')
ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.0, alpha=0.5)
ax2.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.5)

plt.tight_layout()
plt.savefig('figure9a_comparison_charts.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
print("Comparison charts saved as 'figure9a_comparison_charts.png'")
