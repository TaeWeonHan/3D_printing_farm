import matplotlib.pyplot as plt
import pandas as pd
import random

def visualization(export_Daily_Report):
    """
    Gantt 차트를 생성하여 3D 프린팅 팜의 모든 작업자와 프린터를 포함하고 Job별로 고유 색상으로 작업을 시각화합니다.
    :param export_Daily_Report: 시뮬레이션 작업 기록 데이터 리스트
    """
    # 데이터 프레임 변환
    daily_reports = pd.DataFrame(export_Daily_Report)

    # 시간 데이터를 변환
    def convert_time_to_float(time_value):
        if isinstance(time_value, str):  # 문자열인 경우
            try:
                hours, minutes = map(int, time_value.split(":"))
                return hours + minutes / 60.0
            except ValueError:
                return None
        elif isinstance(time_value, (int, float)):  # 숫자형 데이터인 경우
            return time_value
        return None  # 기타 형식은 NaN으로 처리

    # 시간 열 변환
    time_columns = [
        "PRINTING_START", "PRINTING_FINISH",
        "POSTPROCESSING_START", "POSTPROCESSING_FINISH",
        "PACKAGING_START", "PACKAGING_FINISH"
    ]
    for col in time_columns:
        if col in daily_reports.columns:
            daily_reports[col] = daily_reports[col].apply(convert_time_to_float)

    # Job ID별 고유 색상 생성
    def generate_unique_color():
        """고유한 색상을 생성 (RGB 값)"""
        return [random.random() for _ in range(3)]  # R, G, B 값 무작위 생성

    job_colors = {job_id: generate_unique_color() for job_id in daily_reports['JOB_ID'].unique()}

    # 리소스(프린터, 작업자) 목록 생성
    all_printers = sorted(daily_reports["ASSIGNED_PRINTER"].dropna().unique())
    all_post_processors = sorted(daily_reports["ASSIGNED_POSTPROCESS_WORKER"].dropna().unique())
    all_packaging_workers = sorted(daily_reports["ASSIGNED_PACKAGING_WORKER"].dropna().unique())

    resource_labels = (
        [f"Printer {int(printer)}" for printer in all_printers] +
        [f"Post-Processor {int(worker)}" for worker in all_post_processors] +
        [f"Packaging {int(worker)}" for worker in all_packaging_workers]
    )

    # 리소스를 세로축에 표시하기 위해 리소스별로 번호 매기기
    resource_map = {label: idx for idx, label in enumerate(resource_labels)}

    fig, ax = plt.subplots(figsize=(16, 10))

    # 각 작업(Job)을 리소스별로 시각화
    for _, row in daily_reports.iterrows():
        # 프린팅 작업
        if not pd.isna(row["ASSIGNED_PRINTER"]):
            ax.barh(
                resource_map[f"Printer {int(row['ASSIGNED_PRINTER'])}"],
                row["PRINTING_FINISH"] - row["PRINTING_START"],
                left=row["PRINTING_START"],
                color=job_colors[row["JOB_ID"]],
                edgecolor='black',
                label=f"Job {row['JOB_ID']}" if f"Job {row['JOB_ID']}" not in ax.get_legend_handles_labels()[1] else ""
            )
        # 후처리 작업
        if not pd.isna(row["ASSIGNED_POSTPROCESS_WORKER"]):
            ax.barh(
                resource_map[f"Post-Processor {int(row['ASSIGNED_POSTPROCESS_WORKER'])}"],
                row["POSTPROCESSING_FINISH"] - row["POSTPROCESSING_START"],
                left=row["POSTPROCESSING_START"],
                color=job_colors[row["JOB_ID"]],
                edgecolor='black'
            )
        # 포장 작업
        if not pd.isna(row["ASSIGNED_PACKAGING_WORKER"]):
            ax.barh(
                resource_map[f"Packaging {int(row['ASSIGNED_PACKAGING_WORKER'])}"],
                row["PACKAGING_FINISH"] - row["PACKAGING_START"],
                left=row["PACKAGING_START"],
                color=job_colors[row["JOB_ID"]],
                edgecolor='black'
            )

    # 세로축 설정
    ax.set_yticks(list(resource_map.values()))
    ax.set_yticklabels(list(resource_map.keys()))
    ax.set_xlabel("Time")
    ax.set_ylabel("Resources")
    ax.set_title("Job Scheduling Gantt Chart")

    # 범례 설정
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right', bbox_to_anchor=(1.15, 1))

    # 레이아웃 조정 및 출력
    plt.tight_layout()
    plt.show()
