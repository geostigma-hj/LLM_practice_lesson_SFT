import pandas as pd

# 读取两个CSV文件 (保持不变)
main_df = pd.read_csv('非遗项目_web_clean.csv')
wiki_df = pd.read_csv('百度百科_clean.csv')

# 新增：创建百科数据字典（项目名称作为键）
wiki_dict = wiki_df.drop_duplicates('项目名称').set_index('项目名称').to_dict(orient='index')

# 保留原始列名用于后续处理 (保持不变)
original_columns = main_df.columns.tolist()

main_df['历史渊源'] = ''

# 新增：逐行处理逻辑
for index, row in main_df.iterrows():
    project_name = row['项目名称']
    wiki_data = wiki_dict.get(project_name, {})
    
    # 填充历史渊源（新增列）
    main_df.at[index, '历史渊源'] = wiki_data.get('历史渊源', '')
    
    # 填充官网描述
    if pd.isna(row['官网描述']) or row['官网描述'] == '':
        main_df.at[index, '官网描述'] = wiki_data.get('相关介绍', row['官网描述'])
    
    # 替换传承人信息
    if wiki_data.get('传承人物', None) not in [None, '']:
        main_df.at[index, '传承人信息'] = wiki_data['传承人物']

# 保持原始列顺序并添加新列 (保持不变)
main_df = main_df[original_columns + ['历史渊源']]

# 保存结果 (保持不变)
main_df.to_csv('final_dataset.csv', index=False, encoding='utf-8-sig')