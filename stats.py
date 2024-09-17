import pandas as pd 
import scipy.stats as stats
df = pd.read_excel("./data/ragas比較.xlsx")
print(df.info())
rater1 = df["人工準確度"]
rater2 = df["RAGAS-answer correctness"]
# 計算斯皮爾曼等級相關係數
spearman_corr, spearman_p = stats.spearmanr(rater1, rater2)
print(f"Spearman correlation: {spearman_corr}, p-value: {spearman_p}")

# 計算肯德爾Tau係數
kendall_tau, kendall_p = stats.kendalltau(rater1, rater2)
print(f"Kendall tau: {kendall_tau}, p-value: {kendall_p}")