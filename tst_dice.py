#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import os
import json
import subprocess
import unittest

version = 'gurgen_0'


def read_test_cases(path_to_json_data):
    if not os.path.isfile(path_to_json_data):
        raise OSError("'{}' does not exists.".format(path_to_json_data))
    with open(path_to_json_data, 'r') as f:
        data = json.loads(f.read())
    return data


def run_version(version_name, **kwargs):
    """
    Метод запускает версию с параметрами, переданными в **kwargs
    """
    dice_rolls = kwargs['number of dice rolls']
    dice_min = kwargs['minimum number of dice']
    dice_max = kwargs['maximum number of dice']
    command = './src/{}'.format(version_name)
    if dice_rolls:
        command += ' {}'.format(dice_rolls)
    if dice_min:
        command += ' {}'.format(dice_min)
    if dice_max:
        command += ' {}'.format(dice_max)
    print('Запускаем программу с параметрами: {}'.format(command))
    result = subprocess.Popen(command, shell=True, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, stdout=subprocess.PIPE).stdout.read()
    print('Результат: {}'.format(result))
    return result

def write_to_log(data):
    with open(r'output_log.txt', 'a') as f:
        f.write(data)


class TestDice(unittest.TestCase):
    def test_non_param(self):
        test_data = {
            "description": "Проверка запуска программы без параметров",
            "number of dice rolls": "",
            "minimum number of dice": "",
            "maximum number of dice": "",
            "expected result": "Wrong arguments count: 0\n"}
        result = run_version(version_name=version, **test_data)
        self.assertEqual(test_data['expected result'], result, test_data["description"])

    def test_one_param(self):
        test_data = {
            "description": "Проверка запуска программы c одним параметров",
            "number of dice rolls": "1",
            "minimum number of dice": "",
            "maximum number of dice": "",
            "expected result": "Wrong arguments count: 1\n"}
        result = run_version(version_name=version, **test_data)
        self.assertEqual(test_data['expected result'], result, test_data["description"])

    def test_two_param(self):
        test_data = {
            "description": "Проверка запуска программы c двумя параметров",
            "number of dice rolls": "1",
            "minimum number of dice": "1",
            "maximum number of dice": "",
            "expected result": "Wrong arguments count: 2\n"}
        result = run_version(version_name=version, **test_data)
        self.assertEqual(test_data['expected result'], result, test_data["description"])

    def test_all_param(self):
        test_data = {
            "description": "Проверка запуска программы cо всеми параметрами (1, 1, 1)",
            "number of dice rolls": "1",
            "minimum number of dice": "1",
            "maximum number of dice": "1",
            "expected result": "Number of turns: 1\nMinimum number of dices: 1\nMaximum number of dices: 1"}
        result = run_version(version_name=version, **test_data)
        self.assertIn(test_data['expected result'], result, test_data["description"])

if __name__ == '__main__':

    test_data = 'test_cases.json'
    test_cases_data = read_test_cases(test_data)
    unittest.main()

    # for test_name, test_data in test_cases_data.items():
    #     write_to_log('\n\n{}\n'.format(test_name))
    #     print(test_name)
    #     for record in test_data:
    #         write_to_log('{}: {}.\n'.format(record, test_data[record]))
    #         print('{}: {}.'.format(record, test_data[record]))
