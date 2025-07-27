from pathlib import Path
import yaml

def build_script_pages():
    '''Builds an `.md` file for each "script" in the linking table and adds an
    entry to the sidebar menu by building `mkdocs.yml` from `mkdocs_input.yml`.
    '''
    linking_table_file = Path('kpf/linking_table.yml')
    with open(linking_table_file, 'r') as f:
        contents = yaml.safe_load(f)
    
    prefix = contents['common'].get('prefix')
    
    scriptsdir = Path('docs/scripts/')
    scriptsdir.mkdir(parents=False, exist_ok=True)
    
    packages = {}
    
    mkdocs_config_input = Path(__file__).parent / 'mkdocs_input.yml'
    with open(mkdocs_config_input, 'r') as f:
        mkdocs_config = f.read()
    
    for script in contents['links'].keys():
        full_script = contents['links'].get(script).get('cmd')
        package = full_script.split('.')[0]
        if package not in packages.keys():
            packages[package] = []
        packages[package].append(full_script)
    
    mkdocs_config_file = Path(__file__).parent / 'mkdocs.yml'
    if mkdocs_config_file.exists(): mkdocs_config_file.unlink()
    with open(mkdocs_config_file, 'w') as f:
        f.write(mkdocs_config)
        f.write('    - "Instrument Scripts":\n')
        for package in packages.keys():
            f.write(f'      - "kpf.{package}":\n')
            for script in packages[package]:
                scriptname = script.split('.')[-1]
                f.write(f'        - "{scriptname}": scripts/{scriptname}.md\n')
    
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


def build_OB_parameters_pages():
    parameter_file_path = Path('kpf/ObservingBlocks/')
    parameter_files = ['TargetProperties.yaml',
                       'CalibrationProperties.yaml',
                       'ObservationProperties.yaml',
                       ]
    for pfile in parameter_files:
        with open(parameter_file_path / pfile, 'r') as f:
            properties = yaml.safe_load(f.read())

        lines = f"# {pfile.replace('.yaml', '').replace('Properties', ' Properties')}\n\n"
        for p in properties:
            name = p.get('name').replace('twoMASSID', '2MASSID')
            lines += f"**{name}**: `{p.get('valuetype')}`\n"
            lines += f"  {p.get('comment')}\n\n"

        doc_file = Path('docs') / pfile.replace('.yaml', '.md')
        if doc_file.exists(): doc_file.unlink()
        with open(doc_file, 'w') as d:
            d.write(lines)


if __name__ == '__main__':
    build_script_pages()
    build_OB_parameters_pages()
