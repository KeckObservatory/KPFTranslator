from pathlib import Path
import yaml

linking_table_file = Path('kpf/linking_table.yml')
with open(linking_table_file, 'r') as f:
    contents = yaml.safe_load(f)

prefix = contents['common'].get('prefix')

scriptsdir = Path('docs/scripts/')
scriptsdir.mkdir(parents=False, exist_ok=True)

all_scripts = ['# Scripts\n', '\n']

packages = {}

for script in contents['links'].keys():
    full_script = contents['links'].get(script).get('cmd')
    package = full_script.split('.')[0]
    if package not in packages.keys():
        packages[package] = []
    packages[package].append(full_script)

for package in packages.keys():

    all_scripts.append(f'## {package}\n')

    for script in packages[package]:
        scriptname = script.split('.')[-1]
        print(package, script, scriptname)
        
        md_file = Path(f"docs/scripts/{scriptname}.md")
        if md_file.exists() == True:
            md_file.unlink()
        with open(md_file, 'w') as s:
            s.writelines([f'# `{scriptname}`\n',
                          f'\n',
                          f'::: {prefix}.{script}\n',
                          f'    handler: python\n',
                          f'    options:\n',
                          f'      show_source: true\n',
                          ])
        all_scripts.append(f"* [{scriptname}]({scriptname}.md)\n")

script_list_file = Path('docs/scripts/scripts.md')
if script_list_file.exists() == True:
    script_list_file.unlink()
with open(script_list_file, 'w') as scripts_list:
    scripts_list.writelines(all_scripts)
