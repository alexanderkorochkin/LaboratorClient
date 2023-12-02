# [ref=https://vk.com/im][color=548cb9]ВК[/color][/ref]
import json

with open('help.json', encoding='utf8') as outfile:
    tips = json.load(outfile)

helping = {}

for tip in tips:
    helping[tip[0]] = {'disabled': False if tip[2] else True, 'title': tip[1], 'text': tip[2]}