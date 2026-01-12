import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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

# 为每个benchmark和预取器存储数据
results = {}

for bench in benchmarks:
    bench_data = df[df['Trace'] == bench]
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
# 定义颜色（按照堆叠顺序）
colors = {
    'coverage': '#4CAF50',      # 绿色 - 覆盖率（底部）
    'uncovered': '#FFA726',     # 橙色 - 未覆盖率（中间）
    'overprediction': '#EF5350' # 红色 - 过度预测率（顶部）
}

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

# ==================== 计算每个预取器的平均值 ====================
# 存储每个预取器的所有数据
prefetcher_stats = {pref: {'coverages': [], 'uncovereds': [], 'overpredictions': [], 'totals': []} 
                    for pref in prefetcher_labels}

# 遍历所有benchmark和预取器
for bench in benchmarks:
    if bench in results and 'nopref' in results[bench]:
        baseline_data = results[bench]['nopref']
        
        for pref_label, pref_key in zip(prefetcher_labels, ['spp', 'bingo', 'mlop', 'pythia']):
            if pref_key in results[bench]:
                prefetcher_data = results[bench][pref_key]
                coverage, uncovered, overprediction = calculate_miss_fractions(
                    baseline_data, prefetcher_data
                )
                
                # 存储数据
                prefetcher_stats[pref_label]['coverages'].append(coverage * 100)
                prefetcher_stats[pref_label]['uncovereds'].append(uncovered * 100)
                prefetcher_stats[pref_label]['overpredictions'].append(overprediction * 100)
                prefetcher_stats[pref_label]['totals'].append((coverage + uncovered + overprediction) * 100)

# 计算平均值
avg_stats = {}
for pref_label in prefetcher_labels:
    if prefetcher_stats[pref_label]['coverages']:
        avg_stats[pref_label] = {
            'avg_coverage': np.mean(prefetcher_stats[pref_label]['coverages']),
            'avg_uncovered': np.mean(prefetcher_stats[pref_label]['uncovereds']),
            'avg_overprediction': np.mean(prefetcher_stats[pref_label]['overpredictions']),
            'avg_total': np.mean(prefetcher_stats[pref_label]['totals'])
        }

# ==================== 创建图形 ====================
fig, ax = plt.subplots(figsize=(10, 7))

# x轴位置
x = np.arange(len(prefetcher_labels))
width = 0.6

# 为每个预取器绘制堆叠柱状图
for i, pref_label in enumerate(prefetcher_labels):
    if pref_label in avg_stats:
        stats = avg_stats[pref_label]
        
        # 按照顺序绘制堆叠柱状图：
        # 1. 覆盖率（绿色）- 底部
        # 2. 未覆盖率（橙色）- 中间
        # 3. 过度预测率（红色）- 顶部
        
        # 绘制覆盖率（底部）
        ax.bar(x[i], stats['avg_coverage'], width,
              color=colors['coverage'], alpha=0.9,
              edgecolor='black', linewidth=1.2,
              label='Coverage' if i == 0 else "")
        
        # 绘制未覆盖率（中间，堆叠在覆盖率之上）
        ax.bar(x[i], stats['avg_uncovered'], width,
              bottom=stats['avg_coverage'],
              color=colors['uncovered'], alpha=0.9,
              edgecolor='black', linewidth=1.2,
              label='Uncovered' if i == 0 else "")
        
        # 绘制过度预测率（顶部，堆叠在未覆盖率之上）
        ax.bar(x[i], stats['avg_overprediction'], width,
              bottom=stats['avg_coverage'] + stats['avg_uncovered'],
              color=colors['overprediction'], alpha=0.9,
              edgecolor='black', linewidth=1.2,
              label='Overprediction' if i == 0 else "")
        
        # 在柱子顶部添加总计百分比
        total = stats['avg_total']
        ax.text(x[i], total + 1.5, f'{total:.0f}%',
               ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # 在柱子内部添加各部分百分比
        # 覆盖率部分
        if stats['avg_coverage'] > 5:
            coverage_y = stats['avg_coverage'] / 2
            ax.text(x[i], coverage_y, f'{stats["avg_coverage"]:.0f}%',
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   color='white')
        
        # 未覆盖率部分
        if stats['avg_uncovered'] > 5:
            uncovered_y = stats['avg_coverage'] + stats['avg_uncovered'] / 2
            ax.text(x[i], uncovered_y, f'{stats["avg_uncovered"]:.0f}%',
                   ha='center', va='center', fontsize=10, fontweight='bold')
        
        # 过度预测率部分
        if stats['avg_overprediction'] > 5:
            overpred_y = stats['avg_coverage'] + stats['avg_uncovered'] + stats['avg_overprediction'] / 2
            ax.text(x[i], overpred_y, f'{stats["avg_overprediction"]:.0f}%',
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   color='white')

# 设置图形属性
ax.set_xlabel('Prefetcher', fontsize=13)
ax.set_ylabel('Fraction of Baseline LLC Misses (%)', fontsize=13)
ax.set_xticks(x)
ax.set_xticklabels(prefetcher_labels, fontsize=12)
ax.set_title('Figure 7: Average Coverage and Overprediction of Prefetchers', 
             fontsize=15, fontweight='bold', pad=15)

# 添加网格
ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.8)

# 设置y轴范围
max_total = max([stats['avg_total'] for stats in avg_stats.values()]) if avg_stats else 0
ax.set_ylim(0, max_total * 1.15)

# 添加100%参考线
ax.axhline(y=100, color='red', linestyle='--', linewidth=1.5, alpha=0.7, 
           label='Baseline (100%)')

# 添加图例
legend_elements = [
    mpatches.Patch(facecolor=colors['coverage'], edgecolor='black', linewidth=1.2,
                   label='Coverage', alpha=0.9),
    mpatches.Patch(facecolor=colors['uncovered'], edgecolor='black', linewidth=1.2,
                   label='Uncovered', alpha=0.9),
    mpatches.Patch(facecolor=colors['overprediction'], edgecolor='black', linewidth=1.2,
                   label='Overprediction', alpha=0.9),
    plt.Line2D([0], [0], color='red', linestyle='--', linewidth=1.5,
               label='Baseline (100%)')
]

ax.legend(handles=legend_elements, loc='upper right', fontsize=11, frameon=True)

# 调整布局
plt.tight_layout()

# 保存图形
plt.savefig('figure7_average_coverage_overprediction.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
plt.savefig('figure7_average_coverage_overprediction.pdf', bbox_inches='tight', pad_inches=0.1)

# 显示图形
plt.show()

# ==================== 打印详细数据 ====================
print("\n" + "="*80)
print("DETAILED ANALYSIS FOR FIGURE 7")
print("="*80)

print("\n1. AVERAGE STATISTICS BY PREFETCHER:")
print("-"*70)
print(f"{'Prefetcher':<8} {'Coverage':<10} {'Uncovered':<10} {'Overpred':<10} {'Total':<10} {'Coverage+Uncovered':<20}")
print("-"*70)

for pref_label in prefetcher_labels:
    if pref_label in avg_stats:
        stats = avg_stats[pref_label]
        coverage_uncovered = stats['avg_coverage'] + stats['avg_uncovered']
        print(f"{pref_label:<8} {stats['avg_coverage']:<10.1f} {stats['avg_uncovered']:<10.1f} "
              f"{stats['avg_overprediction']:<10.1f} {stats['avg_total']:<10.1f} "
              f"{coverage_uncovered:<20.1f}")

print("\n2. DETAILED DATA FOR EACH BENCHMARK:")
print("-"*100)

# 创建详细数据表格
detailed_data = []
for bench in benchmarks:
    if bench in results and 'nopref' in results[bench]:
        baseline_data = results[bench]['nopref']
        
        for pref_label, pref_key in zip(prefetcher_labels, ['spp', 'bingo', 'mlop', 'pythia']):
            if pref_key in results[bench]:
                prefetcher_data = results[bench][pref_key]
                coverage, uncovered, overprediction = calculate_miss_fractions(
                    baseline_data, prefetcher_data
                )
                
                detailed_data.append({
                    'Benchmark': bench,
                    'Prefetcher': pref_label,
                    'Coverage_%': coverage * 100,
                    'Uncovered_%': uncovered * 100,
                    'Overprediction_%': overprediction * 100,
                    'Total_%': (coverage + uncovered + overprediction) * 100,
                    'Coverage+Uncovered': (coverage + uncovered) * 100
                })

detailed_df = pd.DataFrame(detailed_data)
print(detailed_df.to_string(index=False, float_format=lambda x: f'{x:.1f}'))

print("\n3. STATISTICAL SUMMARY:")
print("-"*50)

# 计算标准差和范围
for pref_label in prefetcher_labels:
    if pref_label in prefetcher_stats and prefetcher_stats[pref_label]['coverages']:
        coverages = prefetcher_stats[pref_label]['coverages']
        uncovereds = prefetcher_stats[pref_label]['uncovereds']
        overpreds = prefetcher_stats[pref_label]['overpredictions']
        totals = prefetcher_stats[pref_label]['totals']
        
        print(f"\n{pref_label}:")
        print(f"  Coverage: {np.mean(coverages):.1f}% ± {np.std(coverages):.1f}% "
              f"(range: {min(coverages):.1f}% - {max(coverages):.1f}%)")
        print(f"  Uncovered: {np.mean(uncovereds):.1f}% ± {np.std(uncovereds):.1f}% "
              f"(range: {min(uncovereds):.1f}% - {max(uncovereds):.1f}%)")
        print(f"  Overprediction: {np.mean(overpreds):.1f}% ± {np.std(overpreds):.1f}% "
              f"(range: {min(overpreds):.1f}% - {max(overpreds):.1f}%)")
        print(f"  Total: {np.mean(totals):.1f}% ± {np.std(totals):.1f}% "
              f"(range: {min(totals):.1f}% - {max(totals):.1f}%)")

print("\n4. PERFORMANCE RANKING:")
print("-"*50)

# 按覆盖率排名
coverage_ranking = sorted([(pref, avg_stats[pref]['avg_coverage']) 
                          for pref in avg_stats.keys()], 
                         key=lambda x: x[1], reverse=True)

print("\nRanking by Coverage (highest to lowest):")
for rank, (pref, coverage) in enumerate(coverage_ranking, 1):
    print(f"  {rank}. {pref}: {coverage:.1f}%")

# 按过度预测率排名（越低越好）
overpred_ranking = sorted([(pref, avg_stats[pref]['avg_overprediction']) 
                          for pref in avg_stats.keys()], 
                         key=lambda x: x[1])

print("\nRanking by Overprediction (lowest to highest):")
for rank, (pref, overpred) in enumerate(overpred_ranking, 1):
    print(f"  {rank}. {pref}: {overpred:.1f}%")

# 计算效率（覆盖率/总预取率）
print("\nEfficiency (Coverage / Total Prefetches):")
for pref_label in prefetcher_labels:
    if pref_label in avg_stats:
        stats = avg_stats[pref_label]
        if stats['avg_total'] > 0:
            efficiency = stats['avg_coverage'] / stats['avg_total'] * 100
            print(f"  {pref_label}: {efficiency:.1f}%")

print("\n5. INTERPRETATION:")
print("-"*50)
print("""
- Coverage: Percentage of baseline LLC load misses that were correctly prefetched
- Uncovered: Remaining LLC load misses after prefetching (should be ~100% - Coverage)
- Overprediction: Additional LLC accesses due to incorrect prefetches
- Total: Coverage + Uncovered + Overprediction
- A good prefetcher has high Coverage and low Overprediction
- Coverage + Uncovered should be approximately 100% for each prefetcher
""")
