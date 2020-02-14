from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QWidget, QTableWidgetItem
from PyQt5.QtWidgets import QFileDialog
from windows_interfaces.main_window import Ui_MainWindow
from windows_interfaces.table_window import Ui_TableForm
import sys
import os
import csv
import xlsxwriter
import sqlite3


class ExamCheckerMainForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.ok_button.clicked.connect(self.show_table)
        self.info_button.clicked.connect(self.show_info)
        self.setFixedSize(self.size())

    def show_table(self):
        school_number = self.school_spinbox.value()
        teacher_initials = self.initiels_lineedit.text()
        date = self.date_lineedit.text()

        if len(teacher_initials.split(" ")) != 3:
            QMessageBox.critical(
                self, "Ошибка!", "Было неправильно введено ФИО учителя!", QMessageBox.Ok
            )
            return

        if len(date.split(".")) != 3:
            QMessageBox.critical(
                self, "Ошибка!", "Была неправильно введена дата!", QMessageBox.Ok
            )
            return
        else:
            day, month, year = map(int, date.split("."))
            if day < 1 or day > 31 or month < 1 or month > 12 or year < 0:
                QMessageBox.critical(
                    self, "Ошибка!", "Была неправильно введена дата!", QMessageBox.Ok
                )
                return

        self.table_window = ExamCheckerWidget(school_number, teacher_initials, date)
        self.table_window.show()

    def show_info(self):
        # TODO: показ информации о работе с программой
        pass


class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()


class ExamCheckerWidget(QWidget, Ui_TableForm):
    def __init__(self, school_number, teacher_initials, date):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.size())

        self.school_number = school_number
        self.teacher_initials = teacher_initials
        self.date = date

        window_title = str(school_number) + "--" + teacher_initials + "--" + date
        self.setWindowTitle(window_title)

        fields = [
            "ФИО ученика", "Номер варианта", "Класс",
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
            "13.1", "13.2", "14.1", "14.2", "14.3", "15.1", "15.2", "Результат",
            "Итоговый балл"
        ]
        self.balls_tablewidget.setColumnCount(len(fields))
        self.balls_tablewidget.setHorizontalHeaderLabels(fields)
        self.balls_tablewidget.resizeColumnsToContents()

        self.add_student_button.clicked.connect(self.add_student)
        self.remove_student_button.clicked.connect(self.remove_student)

        self.save_button.clicked.connect(self.save_table)
        self.csv_button.clicked.connect(self.export_into_csv)
        self.xlsx_button.clicked.connect(self.export_into_xlsx)
        self.delete_table_button.clicked.connect(self.delete_table)

        self.update_balls_button.clicked.connect(self.count_balls)

        self.load_table()

    def load_table(self):
        filename = "-".join([str(self.school_number), self.teacher_initials, self.date]) + ".db"
        if not os.path.exists("balls_databases/" + filename):
            return
        connection = sqlite3.connect("balls_databases/" + filename)
        cursor = connection.cursor()
        data = cursor.execute("SELECT * FROM student_information").fetchall()
        for row in data:
            index, row_data = row[0], row[1:]
            self.balls_tablewidget.setRowCount(index + 1)
            for j, item in enumerate(row_data):
                self.balls_tablewidget.setItem(index, j, QTableWidgetItem(str(item)))
        self.balls_tablewidget.resizeColumnsToContents()

    def count_balls(self):
        if not os.path.exists("variants"):
            os.mkdir("variants")
        for i in range(self.balls_tablewidget.rowCount()):
            variant = self.balls_tablewidget.item(i, 1).text()
            variant_path = "variants/" + variant + ".txt"
            if not os.path.exists(variant_path):
                QMessageBox.critical(
                    self, "Ошибка", f'Варианта "{variant}" не существует (строка {i + 1})',
                    QMessageBox.Ok
                )
                return
            try:
                with open(variant_path, mode="r", encoding="utf-8") as variant_file:
                    variant_data = variant_file.read().split("\n")
                    variant_data = list(map(lambda x: x.strip(), variant_data))
            except OSError as error:
                QMessageBox.critical(self, "Ошибка", error.strerror, QMessageBox.Ok)
                return

            all_tasks_data = []
            for j in range(3, self.balls_tablewidget.columnCount() - 2):
                all_tasks_data.append(self.balls_tablewidget.item(i, j).text())

            balls = 0
            for j in range(12):
                if all_tasks_data[j] == variant_data[j]:
                    balls += 1

            part_2_data = []
            for j in range(12, 19):
                if all_tasks_data[j] == "0б" or all_tasks_data[j] == "0":
                    part_2_data.append(0)
                elif all_tasks_data[j] == "1б" or all_tasks_data[j] == "1":
                    part_2_data.append(1)
                elif all_tasks_data[j] == "2б" or all_tasks_data[j] == "2":
                    part_2_data.append(2)
                elif all_tasks_data[j] == "3б" or all_tasks_data[j] == "3" and 14 <= j <= 16:
                    part_2_data.append(3)
                else:
                    part_2_data.append(0)
            task13_ball = [part_2_data[0], part_2_data[1]]
            task14_ball = [part_2_data[2], part_2_data[3], part_2_data[4]]
            task15_ball = [part_2_data[5], part_2_data[6]]
            balls += max(task13_ball) + max(task14_ball) + max(task15_ball)

            mark = None
            if 0 <= balls <= 3:
                mark = "2"
            elif 4 <= balls <= 9:
                mark = "3"
            elif 10 <= balls <= 15:
                mark = "4"
            elif 16 <= balls <= 19:
                mark = "5"
            self.balls_tablewidget.setItem(
                i, self.balls_tablewidget.columnCount() - 2, QTableWidgetItem(str(balls))
            )

            self.balls_tablewidget.setItem(
                i, self.balls_tablewidget.columnCount() - 1, QTableWidgetItem(mark)
            )

        self.balls_tablewidget.resizeColumnsToContents()

    def add_student(self):
        new_size = self.balls_tablewidget.rowCount() + 1
        self.balls_tablewidget.setRowCount(new_size)

        self.balls_tablewidget.setItem(new_size - 1, 0, QTableWidgetItem("Пупкин Василий Иванович"))
        self.balls_tablewidget.setItem(new_size - 1, 1, QTableWidgetItem("demo"))
        self.balls_tablewidget.setItem(new_size - 1, 2, QTableWidgetItem("9А"))

        for i in range(3, self.balls_tablewidget.columnCount() - 2):
            self.balls_tablewidget.setItem(
                new_size - 1, i, QTableWidgetItem("не приступал")
            )

        self.balls_tablewidget.setItem(
            new_size - 1, self.balls_tablewidget.columnCount() - 2, QTableWidgetItem("0")
        )

        self.balls_tablewidget.setItem(
            new_size - 1, self.balls_tablewidget.columnCount() - 1, QTableWidgetItem("2")
        )
        self.balls_tablewidget.resizeColumnsToContents()

    def remove_student(self):
        if not self.balls_tablewidget.selectedIndexes():
            return

        student_row = self.balls_tablewidget.selectedIndexes()[0].row()
        self.balls_tablewidget.removeRow(student_row)

    def write_default_table_data(self):
        filename = "-".join([str(self.school_number), self.teacher_initials, self.date]) + ".db"
        open("balls_databases/" + filename, mode="tw", encoding="utf-8").close()
        connection = sqlite3.connect("balls_databases/" + filename)
        cursor = connection.cursor()
        cursor.execute(
            """CREATE TABLE teacher_information
            (date                   STRING,
            teacher_initials        STRING,
            school_number           STRING
            );"""
        )
        cursor.execute(
            """CREATE TABLE student_information
            (id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            initials                STRING,
            variant                 STRING,
            class                   STRING,
            task1                   STRING,
            task2                   STRING,
            task3                   STRING,
            task4                   STRING,
            task5                   STRING,
            task6                   STRING,
            task7                   STRING,
            task8                   STRING,
            task9                   STRING,
            task10                  STRING,
            task11                  STRING,
            task12                  STRING,
            task13_1                STRING,
            task13_2                STRING,
            task14_1                STRING,
            task14_2                STRING,
            task14_3                STRING,
            task15_1                STRING,
            task15_2                STRING,
            result_balls            STRING,
            mark                    STRING
            );"""
        )
        cursor.execute(
            f"""
            INSERT INTO teacher_information(date, teacher_initials, school_number)
            VALUES ("{self.date}",
            "{self.teacher_initials}", {str(self.school_number)})"""
        )

        connection.commit()
        connection.close()

    def save_table(self):
        self.count_balls()

        filename = "-".join([str(self.school_number), self.teacher_initials, self.date]) + ".db"
        if not os.path.exists("balls_databases"):
            os.mkdir("balls_databases")

        if not os.path.exists("balls_databases/" + filename):
            open("balls_databases/" + filename, mode="tw", encoding="utf-8").close()
            self.write_default_table_data()

        connection = sqlite3.connect("balls_databases/" + filename)
        cursor = connection.cursor()
        cursor.execute(
            f"""DELETE FROM student_information"""
        )
        for i in range(self.balls_tablewidget.rowCount()):
            data_to_write = []
            for j in range(self.balls_tablewidget.columnCount()):
                data_to_write.append(self.balls_tablewidget.item(i, j).text())
            data_to_write = repr(data_to_write)[1:-1]
            cursor.execute(f"""INSERT INTO student_information VALUES ({i}, {data_to_write})""")
        connection.commit()
        connection.close()

    def delete_table(self):
        filename = "-".join([str(self.school_number), self.teacher_initials, self.date]) + ".db"
        if os.path.exists("balls_databases/" + filename):
            try:
                os.remove("balls_databases/" + filename)
            except OSError as error:
                QMessageBox.critical(self, "Ошибка", error.strerror, QMessageBox.Ok)
                return
        self.balls_tablewidget.clear()
        self.balls_tablewidget.setRowCount(0)

        fields = [
            "ФИО ученика", "Номер варианта", "Класс",
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
            "13.1", "13.2", "14.1", "14.2", "14.3", "15.1", "15.2", "Результат",
            "Итоговый балл"
        ]
        self.balls_tablewidget.setColumnCount(len(fields))
        self.balls_tablewidget.setHorizontalHeaderLabels(fields)
        self.balls_tablewidget.resizeColumnsToContents()

    def export_into_csv(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку") + "/"
        filename = "-".join([str(self.school_number), self.teacher_initials, self.date]) + ".csv"
        if os.path.exists(path + filename):
            os.remove(path + filename)
        with open(path + filename, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([self.balls_tablewidget.horizontalHeaderItem(i).text()
                             for i in range(self.balls_tablewidget.columnCount())])
            for i in range(self.balls_tablewidget.rowCount()):
                row = []
                for j in range(self.balls_tablewidget.columnCount()):
                    item = self.balls_tablewidget.item(i, j)
                    if item is not None:
                        row.append(item.text())
                    else:
                        row.append("NULL")
                writer.writerow(row)

    def export_into_xlsx(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку") + "/"
        filename = "-".join([str(self.school_number), self.teacher_initials, self.date]) + ".xlsx"
        if os.path.exists(path + filename):
            os.remove(path + filename)
        workbook = xlsxwriter.Workbook(path + filename)
        worksheet = workbook.add_worksheet()

        for j in range(self.balls_tablewidget.columnCount()):
            worksheet.write(0, j, self.balls_tablewidget.horizontalHeaderItem(j).text())

        for i in range(self.balls_tablewidget.rowCount()):
            for j in range(self.balls_tablewidget.columnCount()):
                worksheet.write(i + 1, j, self.balls_tablewidget.item(i, j).text())

        balls_count_list = [0] * 20
        marks_count_dict = {"2": 0, "3": 0, "4": 0, "5": 0}
        for i in range(self.balls_tablewidget.rowCount()):
            ball = self.balls_tablewidget.item(i, self.balls_tablewidget.columnCount() - 2).text()
            mark = self.balls_tablewidget.item(i, self.balls_tablewidget.columnCount() - 1).text()
            marks_count_dict[mark] += 1
            balls_count_list[int(ball)] += 1

        worksheet.write_row(
            self.balls_tablewidget.rowCount() + 2, 0, ["Оценка", "Частота встречаемости оценки"]
        )
        for i, (k, v) in enumerate(marks_count_dict.items()):
            worksheet.write_row(self.balls_tablewidget.rowCount() + i + 3, 0, [k, v])

        worksheet.write_row(
            self.balls_tablewidget.rowCount() + 2, 4, ["Балл", "Частота встречаемости балла"]
        )
        for i, count in enumerate(balls_count_list):
            worksheet.write_row(
                self.balls_tablewidget.rowCount() + i + 3, 4, [str(i), count]
            )
        workbook.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    exam_checker = ExamCheckerMainForm()
    exam_checker.show()
    sys.exit(app.exec())
