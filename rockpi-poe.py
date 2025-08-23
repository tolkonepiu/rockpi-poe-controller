#!/usr/bin/env python3
# Based on https://github.com/radxa/23w-poe/blob/master/src/usr/bin/rockpi-poe.py
import sys
import os
import time
import mraa

conf = {}
try:
    pin16 = mraa.Gpio(16)
except Exception:  # pin16 not available on v1.3
    pin16 = None
try:
    pin13 = mraa.Pwm(13)
    pin13.period_ms(13)
    pin13.enable(True)
except Exception:
    pin13 = None


def read_sensor_temp():
    # 42, the answer to life, the universe, and everything
    v2t = lambda x: 42 + (960 - x) * 0.05  # noqa
    with open('/sys/bus/iio/devices/iio:device0/in_voltage0_raw') as f:
        t = v2t(int(f.read().strip()))
    return t


def read_soc_temp(n=0):  # cpu:0  gpu:1
    with open('/sys/class/thermal/thermal_zone{0}/temp'.format(n)) as f:
        t = int(f.read().strip()) / 1000.0
    return t


def read_temp():
    t1 = read_sensor_temp()
    t2 = read_soc_temp(0)
    t3 = read_soc_temp(1)
    return max(t1, t2, t3)


def read_conf():
    conf['lv0'] = int(os.getenv('POE_LV0', 40))
    conf['lv1'] = int(os.getenv('POE_LV1', 45))
    conf['lv2'] = int(os.getenv('POE_LV2', 50))
    conf['lv3'] = int(os.getenv('POE_LV3', 55))


def change_dc(dc, cache={}):
    if dc != cache.get('dc'):
        pin13.write(dc)
        cache['dc'] = dc


def turn_off():
    try:
        pin16.dir(mraa.DIR_OUT)
        pin16.write(0)
    finally:
        change_dc(1.0)


def turn_on():
    try:
        pin16.dir(mraa.DIR_OUT)
        pin16.write(1)
    finally:
        change_dc(0.0)

    read_conf()

    while True:
        t = read_temp()
        if t >= conf['lv3']:
            print('100%')
            change_dc(0.0)
        elif t >= conf['lv2']:
            print('75%')
            change_dc(0.25)
        elif t >= conf['lv1']:
            print('50%')
            change_dc(0.5)
        elif t >= conf['lv0']:
            print('25%')
            change_dc(0.75)
        else:
            print('turn off')
            change_dc(1.0)
        time.sleep(10)


def main():
    try:
        target = sys.argv[1].strip()
        if target == 'start':
            turn_on()
        elif target == 'stop':
            turn_off()
    except KeyboardInterrupt:
        turn_off()
    except Exception as ex:
        print(ex)
        print('using python3 rockpi-poe.py start|stop')


if __name__ == '__main__':
    main()
