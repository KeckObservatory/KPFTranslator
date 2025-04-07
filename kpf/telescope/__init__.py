import ktl

from kpf import cfg


def KPF_is_selected_instrument():
    dcsint = cfg.getint('telescope', 'telnr', fallback=1)
    INSTRUME = ktl.cache(f'dcs{dcsint}', 'INSTRUME').read()
    return INSTRUME in ['KPF', 'KPF-CC']
