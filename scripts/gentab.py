from textwrap import wrap, indent
from decotengu import ZH_L16B, ZH_L16C
import math

LOG_2 = 0.6931471805599453
MAX_DEPTH = 24


def exposure(config, gas, t):
    exp_tab = getattr(config, gas + '_HALF_LIFE')
    return (math.exp(-t / 60 * math.log(2) / hl) for hl in exp_tab)


def str_exp(exp):
    s = ', '.join('{:.16f}'.format(e) for e in exp)
    s = wrap(s)
    s = '\n'.join(s)
    s = indent(s, ' ' * 4)
    s = '(\n{s}\n)'.format(s=s)
    return s


def print_tab(config, gas):
    name = config.__name__

    print('{}_{}_EXP_HALF_LIFE_TIME = ('.format(name, gas))
    ds = 3
    de = MAX_DEPTH
    dt = 18
    for t in range(ds * 6, de * 6 + dt, dt):
        exp = exposure(config, gas, t)
        h = '# {}m, {}s\n'.format(t / 18 * 3, t)
        s = str_exp(exp)
        print(indent(h + s + ',', '    '))
    print(')\n')

    exp = exposure(config, gas, 6)
    s = str_exp(exp)
    print('# 6s')
    print('{}_{}_EXP_HALF_LIFE_1M = {}\n'.format(name, gas, s))

    exp = exposure(config, gas, 12)
    s = str_exp(exp)
    print('# 12s')
    print('{}_{}_EXP_HALF_LIFE_2M = {}\n'.format(name, gas, s))

    exp = exposure(config, gas, 60)
    s = str_exp(exp)
    print('# 1min')
    print('{}_{}_EXP_HALF_LIFE_10M = {}\n'.format(name, gas, s))


print_tab(ZH_L16B, 'N2')
print_tab(ZH_L16B, 'HE')
print_tab(ZH_L16C, 'N2')
print_tab(ZH_L16C, 'HE')
