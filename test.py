import pandas as pd
import json

# 读取 Excel 文件（假设 sheet 第一个）
df = pd.read_excel("实验课课表.xls", header=None)

# 提取表头（星期几）
days = df.iloc[1, 1:].tolist()  # 第一行第2列开始是星期一~星期日
print(days)
# 提取第几节（第1列）
sections = df.iloc[1:, 0].tolist()  # 第二行开始是第1节~第6节
print(sections)

# 构造课程列表
course_list = []

for i, section in enumerate(sections[1:]):  # 遍历第几节
    for j, day in enumerate(days):      # 遍历星期几
        cell = df.iat[i + 2, j + 1]      # 加1是因为表头被跳过
        if pd.notna(cell):              # 如果这个格子有课
            # 有些单元格可能包含多个课程（用换行分隔），逐个处理
            for course in str(cell).split('\n'):
                if course.strip():  # 忽略空行
                    course_name = course.split('(')[0].strip()
                    teacher_name = course.split('(')[1].split('；')[0].strip()
                    location = course.split('；')[-1].split(')')[0].strip()
                    if location == '全周':
                        location = None
                    course_list.append({
                        "course": course_name,
                        "teacher": teacher_name,
                        "location": location,
                        "day": str(day).strip(),
                        "section": str(section).strip()
                    })

print(course_list)
# 保存为 JSON
with open("实验课课表.json", "w", encoding="utf-8") as f:
    json.dump(course_list, f, ensure_ascii=False, indent=4)
