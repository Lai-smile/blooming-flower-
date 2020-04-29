# Created by mqgao at 2019/3/19

"""
Feature: #Enter feature name here
# Enter feature description here

Scenario: #Enter scenario name here
# Enter steps here

Test File Location: # Enter
"""
import gerber
import os
from gerber.render import GerberCairoContext


gm2_dir = '/Users/mqgao/PycharmProjects/auto-pcb-ii/tokenization/gerber_tokenization/data/gerbers'

for i, f in enumerate(os.listdir(gm2_dir)):
    print(i)
    gerber_obj = gerber.read(os.path.join(gm2_dir, f))

    ctx = GerberCairoContext()

    gerber_obj.render(ctx)

    ctx.dump('test-gerber-{}.png'.format(i))

    print('generate end!')
