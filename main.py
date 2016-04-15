#!/usr/bin/python

import logging
import os.path
import random
import string
from datetime import datetime
from openpyxl import load_workbook
from optparse import OptionParser
from subprocess import Popen, STDOUT, PIPE


def main():

    parser = OptionParser()
    parser.add_option("-c", "--csv", dest="csv_dir", default="./csv",
                      help="Directory containing csv files of reports")
    parser.add_option("-r", "--reports", dest="reports_dir", default="./reports",
                      help="Directory containing reports")
    parser.add_option("-t", "--timesheets", dest="timesheets_dir", default="./timesheets",
                      help="Directory to store generated timesheets")
    parser.add_option("-g", "--generate", dest="generate", default="all",
                      help="csv, timesheets, all [default: all]")
    parser.add_option("-s", "--grades", dest="grades_file", default="./grades.txt",
                      help="File containing grades")

    (options, args) = parser.parse_args()

    if options.generate in ['csv', 'all']:
        for file in os.listdir(options.reports_dir):
            if file.endswith(".pdf"):
                filepath = os.path.join(options.reports_dir, file)
                generate_csv(filepath, options.csv_dir)

    if options.generate in ['timesheets', 'all']:
        for file in os.listdir(options.csv_dir):
            if file.endswith(".csv"):
                filepath = os.path.join(options.csv_dir, file)
                f = open(filepath, 'r')
                content = f.read()

                spaced_tables = parse_data(content)
                kv = get_details(spaced_tables[0])
                name = kv["Name"].rstrip()
                period = kv["Period"]
                grade = get_grade(kv["Employee Number"], options.grades_file)
                time_bookings = calculate_time_bookings(spaced_tables[3:-8])
                generate_timesheet(
                    name, period, grade, time_bookings, options.timesheets_dir)
                f.close()
            else:
                print "{} is an invalid file".format(file)


def get_grade(employee_number, grades_file):

    try:
        f = open(grades_file, 'r')
    except IOError:
        logging.error('Failed to open grades file')
        raise
    content = f.readlines()
    if len(content) == 0:
        logging.error('Grade file is empty')
        raise Exception
    grade = ""
    for line in content:
        if employee_number in line:
            grade = line.split()[1]

    f.close()

    return grade


def generate_csv(filepath, output_dir):

    randomint = random.randint(1,1000)
    output_filepath = os.path.join(output_dir, "{}{}".format(randomint, '.csv'))

    p = Popen(['java', '-jar', './tabula-0.9.0-SNAPSHOT-jar-with-dependencies.jar',
               filepath, '-o', output_filepath, '-f', 'CSV', '-r'],
              stdout=PIPE, stderr=STDOUT)
    p.wait()


def parse_data(data):

    tables = data.split("\n")
    i = 0
    spaced_tables = []
    while i < (len(tables)-1):
        spaced_tables.append(tables[i].split("\t"))
        i += 1

    return spaced_tables


def get_details(spaced_tables):

    details = spaced_tables[0].split("\r")
    kv = {}
    for detail in details:
        try:
            kv[detail.split(" : ")[0].strip('"')] = detail.split(" : ")[1]
        except IndexError:
            pass

    return kv


def calculate_time_bookings(time_bookings):

    project_bookings = {}

    for project in time_bookings:
        project = project[0].split(',')
        if 'APT' in project[0]:
            continue
        else:
            project_code = project[0]
        bookable = True if project[1] != 'NBT' else False
        #do something with total_time
        total_time = project[3]

        day_bookings = {}
        for i in range(5,36):
            try:
                day_bookings[i-4] = '1' if project[i] == "7.50" else '0'
            except IndexError:
                pass
        project_bookings[project_code] = {
            "bookable":bookable, "total_time":total_time, "day_bookings":day_bookings}

    return project_bookings


def generate_timesheet(name, period, grade, time_bookings, output_dir):

    workbook = load_workbook('template.xlsx')
    worksheet = workbook.get_sheet_by_name('Supplier Timesheet')

    month = period.split()[0]
    year = int(period.split()[1])
    worksheet['C8'] = month
    worksheet['C9'] = year
    worksheet['C11'] = 'PO NUMBER'

    count = 0
    for key in time_bookings:

        cell_refs = generate_cell_refs(count)
        worksheet[cell_refs.pop(0)] = name
        worksheet[cell_refs.pop(0)] = grade
        worksheet[cell_refs.pop(0)] = key

        for day in time_bookings[key]["day_bookings"].keys():
            try:
                cell_ref = cell_refs.pop(0)
                date_object = datetime.strptime('{} {} {}'.format(
                    year, month, day), '%Y %B %d')

                if date_object.isoweekday() not in [6,7]:
                    worksheet[cell_ref] = int(time_bookings[key]["day_bookings"][day])

            except ValueError:
                pass
        count =+ 1

    filename = 'Timesheet_{}_{}{}.xlsx'.format(
        name.replace(',',"").replace(" ",""), month, year)
    filepath = os.path.join(output_dir, filename)
    workbook.save(filepath)


def generate_cell_refs(index):

    cell_refs = []
    for i in range(1,26):
        cell_refs.append("{}{}".format(string.uppercase[i], str(index+15)))

    for i in range(0,9):
        cell_refs.append(
            "{}{}{}".format(string.uppercase[0], string.uppercase[i], str(index+15)))

    return cell_refs


if __name__ == "__main__":
    main()
