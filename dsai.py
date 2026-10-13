import json
from datetime import datetime, date, timedelta
from ics import Calendar, Event


# ====================== 数据模型类 ======================
class CoursePlan:
    def __init__(self, course, date, start_time, end_time, status="NORMAL", final_alarm=None):
        self.course = course
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        self.final_alarm = final_alarm


# ====================== 导出JSON ======================
def save_json(plans, out_path, avg_snooze):
    out_list = []
    for p in plans:
        out_list.append({
            "course": p.course,
            "date": str(p.date),
            "start_time": str(p.start_time),
            "end_time": str(p.end_time),
            "status": p.status,
            "final_alarm": p.final_alarm
        })
    result = {
        "avg_snooze_minutes": avg_snooze,
        "schedule": out_list
    }
    txt = json.dumps(result, indent=2, ensure_ascii=False)
    if out_path is not None:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(txt)
    return txt


# ====================== 生成ICS日历闹钟 ======================
def make_ics(plans, out_path):
    c = Calendar()
    for p in plans:
        if p.status == "ALARM" and p.final_alarm:
            hh, mm = p.final_alarm.split(":")
            alarm_dt = datetime.combine(p.date, datetime.strptime(f"{hh}:{mm}", "%H:%M").time())
            e = Event()
            e.name = f"⏰ Alarm {p.course}"
            e.begin = alarm_dt
            e.duration = timedelta(minutes=10)
            e.description = f"Smart alarm for {p.course}"
            c.events.add(e)
    ics_str = str(c)
    if out_path is not None:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(ics_str)
    return ics_str


# ====================== 解析 CSV / TXT课表（保留） ======================
def parse_timetable_text(file_path):
    """读取csv/txt课表文件"""
    plans = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(",")
        # 格式示例: 课程名,2026-10-13,09:00,12:00
        course_name, date_str, start_str, end_str = parts[0], parts[1], parts[2], parts[3]
        plan_date = date.fromisoformat(date_str)
        plans.append(CoursePlan(
            course=course_name,
            date=plan_date,
            start_time=start_str,
            end_time=end_str
        ))
    return plans


# ====================== 解析snooze数据（可选） ======================
def parse_snooze_csv(file_path):
    """读取上周赖床数据，返回平均贪睡分钟"""
    total = 0
    count = 0
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        delay_min = int(line)
        total += delay_min
        count +=1
    if count == 0:
        return 0
    return total / count


# ====================== 核心计算：生成推荐闹钟【已修复bug】 ======================
def calculate_alarm_plans(plans, avg_snooze_min):
    result_plans = []
    for p in plans:
        # 解析课程开始时间
        hh, mm = p.start_time.split(":")
        # 修复点：使用datetime.time 只构造时分，不需要年月日
        class_start = datetime.combine(p.date, datetime.time(int(hh), int(mm)))
        # 预留通勤+贪睡缓冲
        wakeup_time = class_start - timedelta(minutes= 25 + avg_snooze_min)
        alarm_str = wakeup_time.strftime("%H:%M")
        new_plan = CoursePlan(
            course=p.course,
            date=p.date,
            start_time=p.start_time,
            end_time=p.end_time,
            status="ALARM",
            final_alarm=alarm_str
        )
        result_plans.append(new_plan)
    return result_plans


# ====================== 文件入口（图片上传禁用） ======================
def load_timetable_file(file_path):
    """读取上传文件，图片功能关闭，仅支持 .csv / .txt"""
    if file_path.lower().endswith((".csv", ".txt")):
        return parse_timetable_text(file_path)
    else:
        raise Exception("Image upload function temporarily disabled. Please upload CSV or TXT timetable file only.")


# ====================== 主运行入口【内置样例，不需要外部csv文件】 ======================
if __name__ == "__main__":
    # 直接内置课表测试数据，不用读取timetable.csv
    raw_plans = [
        CoursePlan(
            course="Math",
            date=date(2026,10,13),
            start_time="09:00",
            end_time="11:00"
        ),
        CoursePlan(
            course="AI Lecture",
            date=date(2026,10,14),
            start_time="14:00",
            end_time="16:00"
        )
    ]

    # 模拟平均贪睡时长（10分钟），不再读取snooze.csv
    avg_delay = 10

    # 计算闹钟
    alarm_plans = calculate_alarm_plans(raw_plans, avg_delay)

    # 输出文件
    save_json(alarm_plans, "output.json", avg_delay)
    make_ics(alarm_plans, "alarm.ics")
    print("✅ Finished! Generated output.json and alarm.ics")
