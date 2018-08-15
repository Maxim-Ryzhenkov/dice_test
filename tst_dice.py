#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import json
import argparse
import unittest
import subprocess
from functools import wraps


class Gurgen(object):
    def __init__(self, version, params=None):
        self.version = version
        self.params = params
        self.error_msg = None
        self.game_results = self._get_game_result()

    def _parse_output(self, output):
        if "Number of turns" not in output:
            return output

        output = output.strip().split("\n")
        output.reverse()
        parsed_output = {'Game info': {
            'Number of turns': re.search(r'Number of turns: (\d+)', output.pop()).group(1),
            'Minimum number of dices': re.search(r'Minimum number of dices: (\d+)', output.pop()).group(1),
            'Maximum number of dices': re.search(r'Maximum number of dices: (\d+)', output.pop()).group(1)},
                        'Results': []}
        while output:
            dices = sorted([int(num) for num in re.findall(r'\b\d+', output.pop())])
            result = re.search(r'Result: (\d+)', output.pop()).group(1)
            parsed_output['Results'].append({'Dices': dices,
                                             'Result': result,
                                             'Sum verification': self._check_dices_sum(dices, result)})
        return parsed_output

    def run(self):
        """Метод запускает версию с параметрами"""
        command = './src/{}'.format(self.version)
        if self.params:
            command += ' {}'.format(self.params)
            print('Запускаем программу с параметрами: {}'.format(command))
        else:
            print('Запускаем программу без параметров: {}'.format(command))
        result = subprocess.Popen(command, shell=True, stderr=subprocess.STDOUT, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE).stdout.read()
        print('Результат: {}'.format(result))
        return result

    def _get_game_result(self):
        """Метод возвращает распарсенный вывод программы"""
        res = self._parse_output(self.run())
        if isinstance(res, str):
            self.error_msg = res
            return None
        return self._parse_output(self.run())

    @staticmethod
    def _dices_sum(dices):
        sum = 0
        if dices == [1, 2, 3, 4, 5]:
            return 150
        for dice in dices:
            if dice == 5:
                sum += 5
            elif dice == 1:
                sum += 10
        return sum

    def _check_dices_sum(self, dices, result):
        return self._dices_sum(dices) == int(result)


def run_until_you_drop_a_combination(version, params, wait_combination, drop_limit=9999):
    """Метод запускает программу до тех пор пока не выпадет нужная комбинация,
    или пока лимит бросков не будет превышен.
    !!! Вызывать метод с одним броском кубиков в аргументах. (1 x x) !!!
    :return  словарь со списком выпавших чисел и их суммой{'Dices': [1, 2, 4], 'Result': 10]}
    """
    for i in range(drop_limit):
        results = Gurgen(version, params).game_results
        if results['Results'][0]['Dices'] == sorted(wait_combination):
            return {'Dices': results['Results'][0]['Dices'],
                    'Result': results['Results'][0]['Result']}
    return False


def write_to_log(data):
    with open(r'output_log.txt', 'a') as f:
        f.write(data)


def run_with(params, expected):
    """Decorator to load params from json file."""
    def decorator(func_to_decorate):
        @wraps(func_to_decorate)
        def wrapper(self, *args, **kwargs):
            result = Gurgen(ver, params).error_msg
            self.assertEqual(expected, result)
            return func_to_decorate(self)
        return wrapper
    return decorator


class TestDice(unittest.TestCase):

    @run_with(params=None, expected="Wrong arguments count: 0\n")
    def test_non_param(self):
        """Проверка запуска программы без аргументов"""

    @run_with(params='1', expected="Wrong arguments count: 1\n")
    def test_one_param(self):
        """Проверка запуска программы c одним аргументом"""

    def test_two_param(self):
        """Проверка запуска программы c двумя аргументами"""
        self.assertEqual("Wrong arguments count: 2\n", Gurgen(ver, "1 1").error_msg)

    def test_four_param(self):
        """Проверка запуска программы c четырьмя аргументами"""
        self.assertEqual("Wrong arguments count: 4\n", Gurgen(ver, "1 1 1 1").error_msg)

    @run_with(params='1 1 a', expected="Wrong arguments\n")
    def test_non_param(self):
        """Проверка запуска программы c буквой вместо цифры в аргуметнах"""

    @run_with(params='-1 1 1', expected="Wrong arguments\n")
    def test_negative_number(self):
        """Количество бросков не может быть отрицательным"""

    def test_all_param(self):
        """Проверка запуска программы cо всеми аргументами (1, 1, 1)"""
        self.assertIn("Number of turns: 1\nMinimum number of dices: 1\nMaximum number of dices: 1",
                      Gurgen(ver, "1 1 1").run())

    def test_max_num_dices(self):
        """Проверка, что кубиков не может быть более 5. Запуск c параметрами (1, 1, 6)"""
        self.assertIn("maxDiceCount range error [1..5]", Gurgen(ver, "1 1 6").error_msg)

    def test_min_num_dices(self):
        """Проверка, что кубиков не может быть менее 1. Запуск c параметрами (1, 0, 5)"""
        self.assertIn("Wrong arguments", Gurgen(ver, "1 0 5").error_msg)

    def test_min_max_dice(self):
        """Проверка, что минимальное число кубиков не может быть больше максимального. Запуск c параметрами (1, 5, 1)"""
        self.assertIn("Error: minDiceCount > maxDiceCount", Gurgen(ver, "1 5 1").error_msg)

    def test_max_rounds(self):
        """Проверка, что максимальное число бросков кубиков не может быть более 999999.
        Запуск c параметрами (1000000, 1, 1)"""
        self.assertIn("Error: number of turns > 999999", Gurgen(ver, "1000000 1 1").error_msg)

    def test_min_rounds(self):
        """Проверка, что минимальное число бросков кубиков не может быть менее 1. Запуск c параметрами (0, 1, 1)"""
        self.assertIn("Wrong arguments", Gurgen(ver, "0 1 1").error_msg)

    def test_value_1(self):
        """Проверка того, что 1 = 10 баллов"""
        self.assertIn("10", run_until_you_drop_a_combination(ver, "1 1 1", [1])['Result'])

    def test_value_2(self):
        """Проверка того, что 2 = 0 баллов"""
        self.assertIn("0", run_until_you_drop_a_combination(ver, "1 1 1", [2])['Result'])

    def test_value_3(self):
        """Проверка того, что 3 = 0 баллов"""
        self.assertIn("0", run_until_you_drop_a_combination(ver, "1 1 1", [3])['Result'])

    def test_value_4(self):
        """Проверка того, что 4 = 0 баллов"""
        self.assertIn("0", run_until_you_drop_a_combination(ver, "1 1 1", [4])['Result'])

    def test_value_5(self):
        """Проверка того, что 5 = 5 баллов"""
        self.assertIn("5", run_until_you_drop_a_combination(ver, "1 1 1", [5])['Result'])

    def test_value_6(self):
        """Проверка того, что 6 = 0 баллов"""
        self.assertIn("0", run_until_you_drop_a_combination(ver, "1 1 1", [6])['Result'])

    def test_value_12345(self):
        """"Проверка того, что [1,2,3,4,5] = 150 баллов"""
        self.assertIn("150", run_until_you_drop_a_combination(ver, "1 5 5", [1, 2, 3, 4, 5], drop_limit=6000)['Result'])

    def test_sum_counting(self):
        """"Проверка того, что сумма верно считается на большом числе бросков (1000 1 5)"""
        # Этот тест не то чтобы очень нужен и занимает много времени,
        # но он позволяет проверить корректность сумм на большой выборке.
        results = Gurgen(ver, '1000 1 5').game_results["Results"]
        self.assertTrue([res['Sum verification'] is True for res in results])

    def test_dice_num(self):
        """"Проверка того, что количество кубиков в броске не больше и не меньше заданного диапазона (1000 1 5)"""
        # Этот тест тоже несколько избыточен и занимает много времени,
        # но он позволяет проверить корректность количеств кубиков в броске большой выборке.
        results = Gurgen(ver, '1000 1 5').game_results["Results"]
        self.assertTrue(all([(1 <= len(num['Dices']) <= 5) for num in results]))


def parse_args(args):
    parser = argparse.ArgumentParser(description='Тест странного софта, который бросает кубики')
    parser.add_argument('version', type=str, help='путь к файлу с тестируемой версией приложения')
    return parser.parse_args(args)


if __name__ == '__main__':

    args = parse_args(sys.argv[1:])
    ver = args.version
    del sys.argv[1:]    # удаляем, чтобы unittest.main() не попытался взять параметры себе
    unittest.main()
