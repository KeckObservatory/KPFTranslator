from pathlib import Path
import re
from datetime import datetime, timedelta

import numpy as np
from astropy.io import fits
from astropy.table import Table, Column
from astropy.modeling import models, fitting
from astropy.time import Time
from astroquery.vizier import Vizier
from astropy import units as u

import matplotlib as mpl
from matplotlib import pyplot as plt

from kpf.KPFTranslatorFunction import KPFTranslatorFunction


def fit_fiber_centering_parameters_one_color(hdul, color=None, xcent=335.5, ycent=258.0, plot=True, nplots=4):
    nlayers, ny, nx = hdul[5].data.shape

    if nx > ny:
        cent = xcent
    else:
        cent = ycent
    if color == 0:
        if nx > ny:
            flux_map = hdul[5].data[4][0,:]
        else:
            flux_map = hdul[5].data[4][:,0]
        color_string = 'all'
    else:
        if nx > ny:
            flux_map = hdul[3].data[color-1][0,:]
        else:
            flux_map = hdul[3].data[color-1][:,0]
        color_string = hdul[3].header.get(f"Layer{color}")
    # color_maps = hdul[3].data
    # color_maps_colors = [hdul[3].header.get(f"Layer{i}") for i in [1,2,3]]

    pixel_values = hdul[5].data[0][0,:] if nx > ny else hdul[5].data[1][:,0]
    pixel_strings = [f"{val:.1f}" for val in pixel_values]

    # Build Coupling Model
    # Uses data from Steve Gibson
    resulting_fits = {'0.50': None, '0.70': None, '0.90': None}
    for seeing in resulting_fits.keys():
        
        model_file = Path(__file__).parent / Path(f'Fiber Coupling Model seeing {seeing} arcsec.csv')
        t = Table.read(f"{model_file}", format='ascii.csv')
        pix_scale = 0.058
        model_pix = np.array(t['Fiber_offset_arcsec'])/pix_scale
        model_flux = np.array(t['Percent_thru'])/max(t['Percent_thru'])
        fit0 = models.Polynomial1D(degree=4)
        fitter = fitting.LinearLSQFitter()
        fit = fitter(fit0, model_pix, model_flux)
        resulting_fits[seeing] = (fit, model_pix, model_flux)

    delta_cents = np.linspace(-3,3,61)
    flux_ratios = np.linspace(0.9,1.1,21)
    chisq = np.zeros((3,len(delta_cents),len(flux_ratios)))
    for i,seeing in enumerate(resulting_fits.keys()):
        fit = resulting_fits[seeing][0]
        model_pix = resulting_fits[seeing][1]
        for k,flux_ratio in enumerate(flux_ratios):
            for j,delta_cent in enumerate(delta_cents):
                pixel_offsets = pixel_values - cent - delta_cent
                w = np.where((pixel_offsets > min(model_pix)) & (pixel_offsets < max(model_pix)))
                model = fit(pixel_offsets[w])*max(flux_map)*flux_ratio
                diff = flux_map[w] - model
                chisq[i,j,k] = np.sum(diff**2/model)

    best_i, best_j, best_k = np.unravel_index(chisq.argmin(), chisq.shape)
    best_seeing = list(resulting_fits.keys())[best_i]
    best_flux_ratio = flux_ratios[best_k]
    best_delta_cent = delta_cents[best_j]
    # print(f"Seeing = {best_seeing}")
    # print(f"Flux Adjustment = {best_flux_ratio:.2f}")
    # print(f"  {color_string} Center Position = {cent:.2f} {best_delta_cent:+.2f} = {cent+best_delta_cent:.2f} pix")

    if plot is True:
        plt.subplot(nplots,1,1+color)
        title = f"ChiSq vs. Center Position Adjustment ({color_string})"
        plt.title(title)
        for i,seeing in enumerate(resulting_fits.keys()):
            line = plt.plot(delta_cents, chisq[i,:,best_k], marker='x', label=f"Seeing={seeing}",
                            alpha=1 if i==best_i else 0.2)
            plt.plot(delta_cents, np.ones(len(delta_cents))*min(chisq[i,:,best_k]),
                     linestyle=':', color=line[0].get_c(),
                     alpha=1 if i==best_i else 0.2)
            plt.plot([best_delta_cent,best_delta_cent], [chisq.min(), chisq.max()], 'r-')
        plt.legend(loc='best')
        plt.yscale("log")
        plt.ylabel('Chi Squared')
        if color == nplots-1:
            plt.xlabel('Center Position Offset (pix)')

    return best_delta_cent, cent + best_delta_cent, float(best_seeing)

def fit_fiber_centering_parameters(fgs_cube_file, xcent=335.5, ycent=258.0, plot=False, targname=None):
    hdul = fits.open(fgs_cube_file)
    dcs = []
    cs = []
    wavs = []
    seeing = []
    if plot is True:
        plt.figure(figsize=(12,16))
    ncolors = hdul[3].data.shape[0]
    for i in range(ncolors):
        dc, c, s = fit_fiber_centering_parameters_one_color(hdul, color=i,
                                                            xcent=xcent, ycent=ycent,
                                                            plot=plot, nplots=ncolors)
        dcs.append(dc)
        cs.append(c)
        seeing.append(s)
        wavstring = hdul[3].header.get(f"Layer{i+1}").strip('nm')
        wavs.append(float(wavstring))
    if plot is True:
        plt.show()

    # print(f"Variation in centers = {min(cs):.1f} to {max(cs):.1f} = {max(cs)-min(cs):.1f} pix")
    return cs, wavs, seeing

def fit_2D_fiber_center(fgs_cube_fileX, fgs_cube_fileY, xcent=335.5, ycent=258.0, targname=None):
    hdul = fits.open(fgs_cube_fileX)
    fnmatch = re.match('TipTilt(\d{8})at(\d{6})_GridSearch.fits', fgs_cube_fileY.name)
    if fnmatch is not None and targname is not None:
        utdate = datetime.strptime(f"{fnmatch.group(1)} {fnmatch.group(2)}", "%Y%m%d %H%M%S")
        ut_string = utdate.strftime('%Y-%m-%d %H:%M:%S')
        va = float(hdul[0].header.get('VA'))
        el = float(hdul[0].header.get('EL'))
        dar_offset_x = float(hdul[0].header.get('DAROFF_X'))
        dar_offset_y = float(hdul[0].header.get('DAROFF_Y'))

    Xcenters, wavs, s = fit_fiber_centering_parameters(fgs_cube_fileX, xcent=xcent, plot=False, targname=targname)
    print(f"X seeing = {np.mean(s):.1f}")
    if np.std(s) > 0.01:
        print(f"Seeing varied during run: {s}")
    Ycenters, wavs, s = fit_fiber_centering_parameters(fgs_cube_fileY, ycent=ycent, plot=False, targname=targname)
    print(f"Y seeing = {np.mean(s):.1f}")
    if np.std(s) > 0.01:
        print(f"Seeing varied during run: {s}")
    ncolors = len(Xcenters)-1
    cstep = int(np.floor(256/ncolors))

    fig = plt.figure(figsize=(8,8))
    title = f"{ut_string} UT\n{targname}: EL={el:.1f} deg, DAR_OFFSET=({dar_offset_x:.1f}, {dar_offset_y:.1f})"
    plt.title(title)

    target_pix_x = np.mean(Xcenters) + dar_offset_x
    target_pix_y = np.mean(Ycenters) + dar_offset_y

    tpdelta = np.ceil(max([abs(target_pix_x-xcent), abs(target_pix_y-ycent)]))
    plot_delta = max([9, tpdelta])

    plt.plot([xcent, xcent], [ycent-plot_delta,ycent+plot_delta], 'k-')
    plt.plot([xcent-plot_delta, xcent+plot_delta], [ycent,ycent], 'k-')
    plt.plot([target_pix_x], [target_pix_y], 'kx', ms=10)

    for i,center in enumerate(zip(Xcenters, Ycenters, wavs)):
        xc, yc, wc = center
        try:
            color = mpl.colormaps['bwr'](i*cstep)
        except AttributeError as e:
            from matplotlib import cm
            color = cm.bwr(i*cstep)
        plt.plot([xc], [yc], marker='o', linestyle='',
                 color=color,
                 label=f'{wc:.0f} nm ({xc:.1f}, {yc:.1f})',
#                  label=f'{wc:.0f} nm',
                 markersize=15, alpha=0.7)

    plt.grid()
    plt.xlabel('CURRENT_BASE X')
    plt.ylabel('CURRENT_BASE Y')
    plt.ylim(ycent-plot_delta,ycent+plot_delta)
    plt.yticks(np.arange(ycent-plot_delta,ycent+plot_delta,1))
    plt.xlim(xcent-plot_delta,xcent+plot_delta)
    plt.xticks(np.arange(xcent-plot_delta,xcent+plot_delta,1))
    fig.gca().set_aspect('equal', 'box')
    plt.legend(loc='upper left')
    plotfile = Path(f"{fgs_cube_fileX.name.replace('.fits', '.png').replace('TipTilt', '')}")
    if plotfile.exists(): plotfile.unlink()
    plt.savefig(f"{plotfile}", bbox_inches='tight', pad_inches=0.1)
#    plt.show()


##-------------------------------------------------------------------------
## Fit2DGridSearch
##-------------------------------------------------------------------------
class Fit2DGridSearch(KPFTranslatorFunction):
    '''# Description
    Take two 1D grid search runs (one in X and one in Y) ...

    # Parameters
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        # 20240718at140930_GridSearch.log
        # TipTilt20240718at140930_GridSearch.fits
        log_file_x = Path(args.get('logfileX'))
        fgs_cube_fileX = log_file_x.parent / Path(f'TipTilt{log_file_x.stem}.fits')
        log_file_y = Path(args.get('logfileY'))
        fgs_cube_fileY = log_file_y.parent / Path(f'TipTilt{log_file_y.stem}.fits')

        # Try to determine targname/comment
        try:
            with open(log_file_x) as FO:
                lines = FO.readlines()
            for line in lines[:60]:
                m_comment = re.search("comment: (.*)", line)
                if m_comment is not None:
                    comment = m_comment.groups()[0].strip('\n')
            log.info(f"  Log Comment: {comment}")
        except:
            comment = ''

        fit_2D_fiber_center(fgs_cube_fileX,
                            fgs_cube_fileY,
                            xcent=args.get('xfit'),
                            ycent=args.get('yfit'),
                            targname=comment)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('logfileX', type=str,
            help="The GridSearch log file for the X pixel scan")
        parser.add_argument('logfileY', type=str,
            help="The GridSearch log file for the Y pixel scan")
        parser.add_argument("--xfit", dest="xfit", type=float,
            default=335.5,
            help="The X pixel position to use as the center when overlaying the model.")
        parser.add_argument("--yfit", dest="yfit", type=float,
            default=258,
            help="The X pixel position to use as the center when overlaying the model.")
        return super().add_cmdline_args(parser, cfg)
