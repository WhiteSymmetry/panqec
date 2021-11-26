"""
Routines for extracting plotting threshold.

:Author:
    Eric Huang
"""
import re
import os
import numpy as np
import pandas as pd
from ._hashing_bound import project_triangle, get_hashing_bound
from ..analysis import quadratic


def detailed_plot(
    plt, results_df, error_model, x_limits=None, save_folder=None,
    yscale=None,
):
    """Plot routine on loop.

    Parameters
    ----------
    plt : matplotlib.pyplot
        The matplotlib pyplot reference.
    results_df : pd.Dataframe
        Results table.
    error_model : str
        Name of the error model to filter to.
    x_limits : Optional[Union[List[Tuple[float, float]], str]]
        Will set limits from 0 to 0.5 if None given.
        Will not impose limits if 'auto' given.
    save_folder : str
        If given will save save figure as png to directory.
    yscale : Optional[str]
        Set to 'log' to make yscale logarithmic.
    """
    df = results_df.copy()
    df.sort_values('probability', inplace=True)
    fig, axes = plt.subplots(ncols=3, figsize=(12, 4))
    plot_labels = [
        (0, 'p_est', 'p_se', error_model),
        (1, 'p_x', 'p_x_se', 'Point sector'),
        (2, 'p_z', 'p_z_se', 'Loop sector'),
    ]
    if x_limits is None:
        x_limits = [(0, 0.5), (0, 0.5), (0, 0.5)]

    for (i_ax, prob, prob_se, title) in plot_labels:
        ax = axes[i_ax]
        for code_size in np.sort(df['size'].unique()):
            df_filtered = df[
                (df['size'] == code_size) & (df['error_model'] == error_model)
            ]
            ax.errorbar(
                df_filtered['probability'], df_filtered[prob],
                yerr=df_filtered[prob_se],
                label=df_filtered['code'].iloc[0],
                capsize=1,
                linestyle='-',
                marker='.',
            )
        if yscale is not None:
            ax.set_yscale(yscale)
        if x_limits != 'auto':
            ax.set_xlim(x_limits[i_ax])
            ax.set_ylim(1e-2, 1e0)

        if i_ax == 0:
            paulis = title.split("Pauli")[1]
            pauli_x = paulis.split("X")[1].split("Y")[0][:5]
            pauli_y = paulis.split("Y")[1].split("Z")[0][:5]
            pauli_z = paulis.split("Z")[1][:5]

            title = (
                title.split("Pauli")[0]
                + "Pauli" + " X" + pauli_x
                + " Y" + pauli_y
                + " Z" + pauli_z
            )

        ax.set_title(title)
        ax.locator_params(axis='x', nbins=6)

        ax.set_xlabel('Physical Error Rate')
        ax.legend(loc='best')
    axes[0].set_ylabel('Logical Error Rate')

    if save_folder:
        filename = os.path.join(save_folder, results_df['label'][0])
        plt.savefig(f'{filename}.png')


def update_plot(plt, results_df, error_model):
    """Plot routine on loop."""
    df = results_df.copy()
    df.sort_values('probability', inplace=True)

    for code_size in np.sort(df['size'].unique()):
        df_filtered = df[
            (df['size'] == code_size) & (df['error_model'] == error_model)
        ]
        plt.errorbar(
            df_filtered['probability'], df_filtered['p_est'],
            yerr=df_filtered['p_se'],
            label=df_filtered['code'].iloc[0]
        )
    plt.title(error_model)
    plt.xlabel('Physical Error Rate', fontsize=20)
    plt.ylabel('Logical Error Rate', fontsize=20)
    plt.legend()


def plot_data_collapse(plt, df_trunc, params_opt, params_bs):
    rescaled_p_fit = np.linspace(
        df_trunc['rescaled_p'].min(), df_trunc['rescaled_p'].max(), 101
    )
    f_fit = quadratic(rescaled_p_fit, *params_opt)

    f_fit_bs = np.array([
        quadratic(rescaled_p_fit, *params)
        for params in params_bs
    ])

    for d_val in np.sort(df_trunc['d'].unique()):
        df_trunc_filt = df_trunc[df_trunc['d'] == d_val]
        plt.errorbar(
            df_trunc_filt['rescaled_p'], df_trunc_filt['p_est'],
            yerr=df_trunc_filt['p_se'], fmt='o', capsize=5,
            label=r'$d={}$'.format(d_val)
        )
    plt.plot(
        rescaled_p_fit, f_fit, color='black', linewidth=1, label='Best fit'
    )
    plt.fill_between(
        rescaled_p_fit,
        np.quantile(f_fit_bs, 0.16, axis=0),
        np.quantile(f_fit_bs, 0.84, axis=0),
        color='gray', alpha=0.2, label=r'$1\sigma$ fit'
    )
    plt.xlabel(
        r'Rescaled error probability $(p - p_{\mathrm{th}})d^{1/\nu}$',
        fontsize=16
    )
    plt.ylabel(r'Logical failure rate $p_{\mathrm{fail}}$', fontsize=16)

    error_model = df_trunc['error_model'].iloc[0]
    title = get_error_model_format(error_model)
    plt.title(title)
    plt.legend()


def get_error_model_format(error_model: str, eta=None) -> str:
    if 'deformed' in error_model:
        fmt = 'Deformed'
    else:
        fmt = 'Undeformed'

    if eta is None:
        match = re.search(r'Pauli X(.+)Y(.+)Z(.+)', error_model)
        if match:
            r_x = np.round(float(match.group(1)), 4)
            r_y = np.round(float(match.group(2)), 4)
            r_z = np.round(float(match.group(3)), 4)
            fmt += ' $(r_X, r_Y, r_Z)=({},{},{})$'.format(r_x, r_y, r_z)
        else:
            fmt = error_model
    else:
        fmt += r' $\eta={}$'.format(eta)
    return fmt


def plot_threshold_nearest(plt, p_th_nearest):
    plt.axvline(
        p_th_nearest, color='green', linestyle='-.',
        label=r'$p_{\mathrm{th}}=(%.2f)\%%$' % (
            100*p_th_nearest
        )
    )


def plot_threshold_fss(
    plt, df_trunc, p_th_fss, p_th_fss_left, p_th_fss_right, p_th_fss_se
):

    for d_val in np.sort(df_trunc['d'].unique()):
        df_trunc_filt = df_trunc[df_trunc['d'] == d_val]
        plt.errorbar(
            df_trunc_filt['probability'], df_trunc_filt['p_est'],
            yerr=df_trunc_filt['p_se'],
            fmt='o-', capsize=5, label=r'$d={}$'.format(d_val)
        )
    plt.axvline(
        p_th_fss, color='red', linestyle='-.',
        label=r'$p_{\mathrm{th}}=(%.2f\pm %.2f)\%%$' % (
            100*p_th_fss, 100*p_th_fss_se,
        )
    )
    plt.axvspan(
        p_th_fss_left, p_th_fss_right, alpha=0.5, color='pink'
    )
    plt.xlabel(
        'Error probability $p$',
        fontsize=16
    )
    plt.ylabel(r'Logical failure rate $p_{\mathrm{fail}}$', fontsize=16)
    plt.title(get_error_model_format(df_trunc['error_model'].iloc[0]))
    plt.legend()


def draw_tick_symbol(
    plt, Line2D,
    log=False, axis='x',
    tick_height=0.03, tick_width=0.1, tick_location=2.5,
    axis_offset=0,
):
    x_points = np.array([
        -0.25,
        0,
        0,
        0.25,
    ])*tick_width + tick_location
    if log:
        x_points = 10**np.array(x_points)
    y_points = np.array([
        0,
        0.5,
        -0.5,
        0,
    ])*tick_height + axis_offset
    points = (x_points, y_points)
    if axis != 'x':
        points = (y_points, x_points)
    line = Line2D(
        *points,
        lw=1, color='k',
    )
    line.set_clip_on(False)
    plt.gca().add_line(line)


def format_eta(eta, decimals=4):
    if eta == np.inf:
        return r'\infty'
    elif np.isclose(np.round(eta, decimals) % 1, 0):
        return str(int(np.round(eta, decimals)))
    else:
        return str(np.round(eta, decimals))


def plot_threshold_vs_bias(
    plt, Line2D, error_model_df, main_linestyle='-',
    eta_keys=['eta_x', 'eta_z', 'eta_y'],
    markers=['x', 'o', '^'],
    colors=['r', 'b', 'g'],
    labels=None,
    hashing=True,
    png=None,
):
    cmap = plt.get_cmap("tab10")
    colors = [cmap(3), cmap(0), cmap(2)]
    p_th_key = 'p_th_fss'
    if labels is None:
        labels = [
            r'${}$ bias'.format(eta_key[-1].upper())
            for eta_key in eta_keys
        ]
    inf_replacement = 1000
    for eta_key, color, marker, label in zip(
        eta_keys, colors, markers, labels
    ):
        df_filt = error_model_df[
            error_model_df[eta_key] >= 0.5
        ].sort_values(by=eta_key)
        p_th_inf = df_filt[df_filt[eta_key] == np.inf][p_th_key].iloc[0]
        plt.plot(
            df_filt[eta_key], df_filt[p_th_key],
            linestyle=main_linestyle,
            color=color,
            label=label,
            marker=marker
        )
        plt.plot(
            [
                df_filt[df_filt[eta_key] != np.inf].iloc[-1][eta_key],
                inf_replacement
            ],
            [
                df_filt[df_filt[eta_key] != np.inf].iloc[-1][p_th_key],
                p_th_inf,
            ],
            '--', color=color, marker=marker, linewidth=1
        )
        plt.text(
            inf_replacement,
            p_th_inf + 0.01,
            '{:.3f}'.format(p_th_inf),
            color=color,
            ha='center'
        )

    # Show label for depolarizing data point.
    p_th_dep = error_model_df[error_model_df[eta_key] == 0.5].iloc[0][p_th_key]
    plt.text(0.5, p_th_dep + 0.01, f'{p_th_dep:.3f}', ha='center')

    # Plot the hashing bound curve.
    if hashing:
        eta_interp = np.logspace(np.log10(0.5), np.log10(100), 101)
        interp_points = [
            (
                1/(2*(1 + eta)),
                1/(2*(1 + eta)),
                eta/(1 + eta)
            )
            for eta in eta_interp
        ]
        hb_interp = [
            get_hashing_bound(point)
            for point in interp_points
        ]
        plt.plot(eta_interp, hb_interp, '-.', color='black', label='hashing')
        plt.plot(
            df_filt[eta_key],
            [get_hashing_bound(point) for point in df_filt['noise_direction']],
            'k.'
        )
        plt.plot(
            inf_replacement,
            get_hashing_bound((0, 0, 1)),
            '.'
        )
        plt.plot(
            [
                eta_interp[-1],
                inf_replacement,
            ],
            [
                hb_interp[-1],
                get_hashing_bound((0, 0, 1))
            ],
            '--', color='black', linewidth=1,
        )

    plt.legend()
    plt.xscale('log')
    draw_tick_symbol(plt, Line2D, log=True)
    plt.xticks(
        ticks=[0.5, 1e0, 1e1, 1e2, inf_replacement],
        labels=['0.5', '1', '10', ' '*13 + '100' + ' '*10 + '...', r'$\infty$']
    )
    plt.xlabel(r'Bias Ratio $\eta$', fontsize=16)
    plt.ylabel(r'Threshold $p_{\mathrm{th}}$', fontsize=16)
    if png is not None:
        plt.savefig(png)


def plot_thresholds_on_triangle(
    plt, error_model_df, title='Thresholds',
    colors=['r', 'b', 'g']
):
    label_threshold = 'p_th_fss'
    eta_keys = ['eta_x', 'eta_z', 'eta_y']
    markers = ['x', 'o', '^']
    label_offsets = [(0, 0.1), (0.2, 0), (0, 0.1)]

    plt.plot(*np.array([
        project_triangle(point)
        for point in [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)]
    ]).T, '-', color='gray', linewidth=1)

    p_th_dep = error_model_df[
        error_model_df['eta_z'] == 0.5
    ].iloc[0][label_threshold]
    plt.text(0.1, 0, f'{p_th_dep:.2f}', ha='center')

    for eta_key, color, marker, offset in zip(
        eta_keys, colors, markers, label_offsets
    ):
        df_filt = error_model_df[
            error_model_df[eta_key] >= 0.5
        ].sort_values(by=eta_key)
        plt.plot(
            df_filt['h'], df_filt['v'],
            marker=marker, linestyle='-', color=color,
            label=r'${}$ bias'.format(eta_key[-1].upper()),
        )
        plt.text(
            *np.array(project_triangle(df_filt.iloc[-1]['noise_direction']))
            + offset,
            '{:.2f}'.format(df_filt.iloc[-1][label_threshold]),
            color=color, ha='center',
            fontsize=16
        )
    plt.text(
        *np.array(project_triangle((1, 0, 0))) + [-0.1, -0.1],
        r'$X$',
        ha='center', fontsize=20, color='r'
    )
    plt.text(
        *np.array(project_triangle((0, 1, 0))) + [0.1, -0.1],
        r'$Y$',
        ha='center', fontsize=20, color='g'
    )
    plt.text(
        *np.array(project_triangle((0, 0, 1))) + [0, 0.1],
        r'$Z$',
        ha='center', fontsize=20, color='b'
    )
    plt.axis('off')
    plt.legend(title=title, loc='upper left', title_fontsize=16, fontsize=12)
    plt.gca().set_aspect(1)


def plot_combined_threshold_vs_bias(plt, Line2D, thresholds_df, pdf=None):
    thres_df_filt = thresholds_df[
        thresholds_df['error_model'].str.contains('Deformed')
    ]
    plot_threshold_vs_bias(
        plt, Line2D, thres_df_filt,
        labels=['Z deformed', 'X deformed'],
        hashing=False
    )
    thres_df_filt = thresholds_df[
        ~thresholds_df['error_model'].str.contains('Deformed')
    ]
    plot_threshold_vs_bias(
        plt, Line2D, thres_df_filt,
        eta_keys=['eta_x', 'eta_z'],
        colors=['#ff9999', '#9999ff'],
        labels=['Z undeformed', 'X undeformed'],
        main_linestyle='--',
        hashing=False
    )
    plt.ylim(0, 0.5)
    plt.text(0.5, -0.06, 'Depol.', ha='center')
    if pdf:
        plt.savefig(pdf, bbox_inches='tight')


def plot_crossing_collapse(
    plt, bias_direction, deformed, results_df,
    thresholds_df, trunc_results_df, params_bs_list,
    pdf=None
):
    params_bs_dict = dict(zip(
        thresholds_df['error_model'].values,
        params_bs_list
    ))
    eta_key = f'eta_{bias_direction}'
    plot_thresholds_df = thresholds_df[
        ~(thresholds_df['error_model'].str.contains('Deformed') ^ deformed)
        & (thresholds_df[eta_key] >= 0.5)
    ].sort_values(by=eta_key)
    fig, axes = plt.subplots(
        plot_thresholds_df.shape[0], 2, figsize=(10, 15),
        gridspec_kw={'width_ratios': [1.2, 1]}
    )
    for i, (_, row) in enumerate(plot_thresholds_df.iterrows()):
        plt.sca(axes[i, 0])
        df_trunc = trunc_results_df[
            (trunc_results_df['error_model'] == row['error_model'])
        ]
        df_no_trunc = results_df[
            results_df['error_model'] == row['error_model']
        ].copy()
        df_no_trunc['d'] = results_df['n_k_d'].apply(lambda x: x[2])
        plot_threshold_fss(
            plt, df_no_trunc, row['p_th_fss'], row['p_th_fss_left'],
            row['p_th_fss_right'], row['p_th_fss_se']
        )
        plot_threshold_nearest(
            plt, row['p_th_nearest']
        )
        plt.title(None)
        plt.ylabel(r'$p_{\mathrm{fail}}$')
        plt.gca().tick_params(direction='in')
        if i < plot_thresholds_df.shape[0] - 1:
            plt.gca().tick_params(labelbottom=False, direction='in')
            plt.xlabel(None)
        else:
            plt.xlabel(r'Error Rate $p$')
        plt.gca().minorticks_on()
        plt.gca().tick_params(direction='in', which='minor')
        plt.ylim(0, 0.9)
        plt.xlim(0, 1.5*plot_thresholds_df['p_right'].max())
        plt.gca().get_legend().remove()
        plt.gca().legend(
            plt.gca().get_legend_handles_labels()[1][:1],
            title=r'%s $\eta_%s=%s$' % (
                {True: 'Deformed', False: 'Undeformed'}[deformed],
                bias_direction.upper(),
                format_eta(row[eta_key])
            ),
            title_fontsize=12,
            loc='lower right'
        )

        plt.sca(axes[i, 1])
        plot_data_collapse(
            plt, df_trunc, row['fss_params'],
            params_bs_dict[row['error_model']]
        )
        plt.title(None)
        plt.ylabel(None)
        rescaled_p_vals = trunc_results_df[
            trunc_results_df['error_model'] == row['error_model']
        ]['rescaled_p']
        plt.xlim(
            np.min(rescaled_p_vals) - 0.05,
            np.max(rescaled_p_vals) + 0.05
        )
        plt.gca().tick_params(labelleft=False, axis='y', direction='in')
        if i < plot_thresholds_df.shape[0] - 1:
            plt.gca().tick_params(labelbottom=False, direction='in')
            plt.xlabel(None)
        else:
            plt.xlabel(r'Rescaled Error rate $(p-p_{\mathrm{th}})d^{1/\nu}$')
        plt.gca().get_legend().remove()
        plt.legend(
            ncol=3
        )
        plt.ylim(0, 0.9)
    fig.subplots_adjust(wspace=0.01, hspace=0)
    if pdf:
        plt.savefig(pdf, bbox_inches='tight')


def plot_deformedxps(plt, results_df, pdf=None):
    detailed_plot(
        plt, results_df, 'Deformed Pauli X1.0Y0.0Z0.0',
    )
    if pdf:
        plt.savefig(pdf, bbox_inches='tight')


def plot_deformedzps(plt, results_df, pdf=None):
    detailed_plot(
        plt, results_df, 'Deformed Pauli X0.0Y0.0Z1.0',
    )
    if pdf:
        plt.savefig(pdf, bbox_inches='tight')


def plot_combined_triangles(plt, thresholds_df, pdf=None):
    thres_df_filt = thresholds_df[
        thresholds_df['error_model'].str.contains('Deformed')
    ]
    fig, axes = plt.subplots(nrows=2, figsize=(4, 8))
    plt.sca(axes[0])
    plot_thresholds_on_triangle(
        plt, thres_df_filt, title='Deformed', colors=['r', 'b', 'g']
    )
    thres_df_filt = thresholds_df[
        ~thresholds_df['error_model'].str.contains('Deformed')
    ]
    plt.sca(axes[1])
    plot_thresholds_on_triangle(
        plt, thres_df_filt, title='Undeform.',
        colors=['#ff9999', '#9999ff', '#55aa55']
    )
    if pdf:
        plt.savefig(pdf, bbox_inches='tight')


def plot_crossing_example(
    plt, results_df, thresholds_df, params_bs_list, pdf=None
):
    error_model = 'Deformed Pauli X0.0Y0.0Z1.0'
    row = thresholds_df[thresholds_df['error_model'] == error_model].iloc[0]
    df_no_trunc = results_df[
        results_df['error_model'] == row['error_model']
    ].copy()
    df_no_trunc['d'] = results_df['n_k_d'].apply(lambda x: x[2])
    plot_threshold_fss(
        plt, df_no_trunc, row['p_th_fss'], row['p_th_fss_left'],
        row['p_th_fss_right'], row['p_th_fss_se']
    )
    if pdf:
        plt.savefig(pdf, bbox_inches='tight')


def plot_collapse_example(
    plt, thresholds_df, trunc_results_df, params_bs_list,
    verbose=True, pdf=None
):
    error_model = 'Deformed Pauli X0.0Y0.0Z1.0'
    row = thresholds_df[thresholds_df['error_model'] == error_model].iloc[0]
    df_trunc = trunc_results_df[trunc_results_df['error_model'] == error_model]
    i = thresholds_df['error_model'].tolist().index(error_model)
    plot_data_collapse(plt, df_trunc, row['fss_params'], params_bs_list[i])
    if verbose:
        print(pd.DataFrame(
            {
                'value': row['fss_params'],
                'se': np.std(params_bs_list[i], axis=0)
            },
            index=['p_th', 'nu', 'A', 'B', 'C']
        ))
    if pdf:
        plt.savefig(pdf, bbox_inches='tight')
