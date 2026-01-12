import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
                'LLC_total_miss': data['Core_0_LLC_total_miss']
            }

# ==================== 图1(b): IPC性能提升百分比对比 ====================
# 创建图形
fig, ax = plt.subplots(figsize=(8, 6))

# 定义颜色
ipc_colors = {
    'spp': '#1f77b4',       # 蓝色
    'bingo': '#2ca02c',     # 绿色
    'pythia': '#d62728'     # 红色
}

# 只绘制SPP、Bingo、Pythia三种预取器
prefetchers_to_plot = ['spp', 'bingo', 'pythia']
prefetcher_labels = ['SPP', 'Bingo', 'Pythia']

# 计算每个benchmark和预取器的IPC提升百分比
bench_names = []
all_improvements = {pref: [] for pref in prefetchers_to_plot}

for bench in benchmarks:
    if bench in results and 'nopref' in results[bench]:
        # 获取baseline IPC
        baseline_ipc = results[bench]['nopref']['IPC']
        
        # 为每个预取器计算提升百分比
        for pref in prefetchers_to_plot:
            if pref in results[bench]:
                pref_ipc = results[bench][pref]['IPC']
                # 计算IPC提升百分比：((IPC_prefetcher / IPC_baseline) - 1) × 100%
                improvement_percent = ((pref_ipc / baseline_ipc) - 1) * 100
                all_improvements[pref].append(improvement_percent)
        
        # 简化benchmark名称用于显示
        if bench.startswith('482'):
            bench_names.append('sphinx3')
        elif bench.startswith('459'):
            bench_names.append('GemsFDTD')
        else:
            bench_names.append(bench.split('.')[0])

# 绘制每个benchmark的IPC提升对比
x = np.arange(len(bench_names))
width = 0.25  # 柱状图宽度

# 为每个预取器绘制柱状图
for i, (pref, label) in enumerate(zip(prefetchers_to_plot, prefetcher_labels)):
    improvements = all_improvements[pref]
    offset = (i - 1) * width  # 居中排列
    
    bars = ax.bar(x + offset, improvements, width, 
                  color=ipc_colors[pref], alpha=0.8,
                  edgecolor='black', linewidth=1.0,
                  label=label, zorder=3)
    
    # 在每个柱子上方添加数值标签
    for bar, value in zip(bars, improvements):
        height = bar.get_height()
        # 根据正负值调整标签位置
        if value >= 0:
            va = 'bottom'
            y_offset = 0.5
        else:
            va = 'top'
            y_offset = -0.5
        
        # 格式化数值显示
        value_str = f'{value:+.1f}%' if abs(value) >= 0.1 else f'{value:+.2f}%'
        
        ax.text(bar.get_x() + bar.get_width()/2., height + y_offset,
                value_str, ha='center', va=va, fontsize=9, fontweight='bold')

# 设置图形属性
ax.set_xlabel('Benchmark', fontsize=11)
ax.set_ylabel('IPC Improvement over Baseline (%)', fontsize=11)
ax.set_xticks(x)
ax.set_xticklabels(bench_names, fontsize=10)
ax.set_title('Figure 1(b): IPC Performance Improvement Comparison', 
             fontsize=12, fontweight='bold', pad=15)

# 添加网格
ax.grid(True, alpha=0.3, axis='y', linestyle='--', linewidth=0.5, zorder=0)

# 添加图例
ax.legend(fontsize=10, frameon=True, loc='upper left', ncol=3)

# 添加水平零线
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)

# 设置y轴范围
all_values = []
for pref in prefetchers_to_plot:
    all_values.extend(all_improvements[pref])

if all_values:
    min_val = min(all_values)
    max_val = max(all_values)
    # 为标签留出空间
    margin = (max_val - min_val) * 0.15
    ax.set_ylim(min_val - margin, max_val + margin)

# 调整布局
plt.tight_layout()

# 保存图形
plt.savefig('figure1b_ipc_improvement.png', dpi=300, bbox_inches='tight', pad_inches=0.1)
plt.savefig('figure1b_ipc_improvement.pdf', bbox_inches='tight', pad_inches=0.1)

# 显示图形
plt.show()

# ==================== 打印详细数据 ====================
print("\n" + "="*80)
print("DETAILED IPC IMPROVEMENT ANALYSIS FOR FIGURE 1(b)")
print("="*80)

print("\n1. BASELINE IPC VALUES:")
print("-"*40)
for bench, bench_name in zip(benchmarks, bench_names):
    if bench in results and 'nopref' in results[bench]:
        baseline_ipc = results[bench]['nopref']['IPC']
        print(f"{bench_name}: IPC = {baseline_ipc:.4f}")

print("\n2. IPC IMPROVEMENT OVER BASELINE (%):")
print("-"*60)
print(f"{'Benchmark':<12} {'SPP':<10} {'Bingo':<10} {'Pythia':<10}")
print("-"*60)

for i, (bench, bench_name) in enumerate(zip(benchmarks, bench_names)):
    if bench in results and 'nopref' in results[bench]:
        baseline_ipc = results[bench]['nopref']['IPC']
        
        improvements = []
        for pref, pref_label in zip(prefetchers_to_plot, prefetcher_labels):
            if pref in results[bench]:
                pref_ipc = results[bench][pref]['IPC']
                improvement = ((pref_ipc / baseline_ipc) - 1) * 100
                improvements.append(f"{improvement:+.2f}%")
            else:
                improvements.append("N/A")
        
        print(f"{bench_name:<12} {improvements[0]:<10} {improvements[1]:<10} {improvements[2]:<10}")

print("\n3. AVERAGE IPC IMPROVEMENT (%):")
print("-"*40)
for pref, label in zip(prefetchers_to_plot, prefetcher_labels):
    improvements = all_improvements[pref]
    if improvements:
        avg_improvement = np.mean(improvements)
        print(f"{label}: {avg_improvement:+.2f}%")

print("\n4. RELATIVE PERFORMANCE (Pythia vs others):")
print("-"*50)
if 'pythia' in all_improvements and 'spp' in all_improvements and 'bingo' in all_improvements:
    pythia_avg = np.mean(all_improvements['pythia'])
    spp_avg = np.mean(all_improvements['spp'])
    bingo_avg = np.mean(all_improvements['bingo'])
    
    pythia_vs_spp = pythia_avg - spp_avg
    pythia_vs_bingo = pythia_avg - bingo_avg
    
    print(f"Pythia vs SPP: {pythia_vs_spp:+.2f}% advantage")
    print(f"Pythia vs Bingo: {pythia_vs_bingo:+.2f}% advantage")

# ==================== 创建汇总表格 ====================
print("\n5. DATA SUMMARY TABLE:")
print("-"*80)
summary_data = []
for i, (bench, bench_name) in enumerate(zip(benchmarks, bench_names)):
    if bench in results and 'nopref' in results[bench]:
        row = {'Benchmark': bench_name}
        baseline_ipc = results[bench]['nopref']['IPC']
        row['Baseline_IPC'] = baseline_ipc
        
        for pref, label in zip(prefetchers_to_plot, prefetcher_labels):
            if pref in results[bench]:
                pref_ipc = results[bench][pref]['IPC']
                improvement = ((pref_ipc / baseline_ipc) - 1) * 100
                row[f'{label}_IPC'] = pref_ipc
                row[f'{label}_Improvement'] = improvement
        
        summary_data.append(row)

# 转换为DataFrame并显示
summary_df = pd.DataFrame(summary_data)
print(summary_df.to_string(index=False, float_format=lambda x: f'{x:.3f}' if abs(x) >= 1 else f'{x:.4f}'))
