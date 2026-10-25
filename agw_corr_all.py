import re
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl


def equation(a, b):
    """Return a 1D polynomial."""
    return np.polyval(a, b)


def plot_ci_manual(t, s_err, n, x, x2, y2, ax=None):
    """Return an axes of confidence bands using a simple approach.

    Notes
    -----
    .. math:: \left| \: \hat{\mu}_{y|x0} - \mu_{y|x0} \: \right| \; \leq \; T_{n-2}^{.975} \; \hat{\sigma} \; \sqrt{\frac{1}{n}+\frac{(x_0-\bar{x})^2}{\sum_{i=1}^n{(x_i-\bar{x})^2}}}
    .. math:: \hat{\sigma} = \sqrt{\sum_{i=1}^n{\frac{(y_i-\hat{y})^2}{n-2}}}

    References
    ----------
    .. [1] M. Duarte.  "Curve fitting," Jupyter Notebook.
       http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/CurveFitting.ipynb

    """
    if ax is None:
        ax = plt.gca()

    ci = t * s_err * np.sqrt(1 / n + (x2 - np.mean(x)) ** 2 / np.sum((x - np.mean(x)) ** 2))
    ax.fill_between(x2, y2 + ci, y2 - ci, color=FILL_COLOR, edgecolor=FILL_COLOR)

    return ax


def plot_stat_params(x, y, x_label, y_label):
    p, cov = np.polyfit(x, y, 1, cov=True)  # parameters and covariance from of the fit of 1-D polynom.
    y_model = equation(p, x)  # model using the fit parameters; NOTE: parameters here are coefficients

    # Statistics
    n = x.size  # number of observations
    m = p.size  # number of parameters
    dof = n - m  # degrees of freedom
    t = stats.t.ppf(0.975, n - m)  # t-statistic; used for CI and PI bands

    # Estimates of Error in Data/Model
    resid = y - y_model  # residuals; diff. actual data from predicted values
    chi2 = np.sum((resid / y_model) ** 2)  # chi-squared; estimates error in data
    chi2_red = chi2 / dof  # reduced chi-squared; measures goodness of fit
    s_err = np.sqrt(np.sum(resid ** 2) / dof)  # standard deviation of the error

    # Plotting --------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 6))

    # Data
    ax.plot(
        x, y, "o", color=FILL_COLOR, markersize=8,
        markeredgewidth=1, markeredgecolor="r", markerfacecolor="None"
    )

    # Fit
    ax.plot(x, y_model, "-", color="0.1", linewidth=1.5, alpha=0.5, label="Fit")

    x2 = np.linspace(np.min(x), np.max(x), 100)
    y2 = equation(p, x2)

    # Confidence Interval (select one)
    plot_ci_manual(t, s_err, n, x, x2, y2, ax=ax)
    # plot_ci_bootstrap(x, y, resid, ax=ax)

    # Prediction Interval
    pi = t * s_err * np.sqrt(1 + 1 / n + (x2 - np.mean(x)) ** 2 / np.sum((x - np.mean(x)) ** 2))
    ax.fill_between(x2, y2 + pi, y2 - pi, color="None", linestyle="--")
    ax.plot(x2, y2 - pi, "--", color="0.5", label="95% Prediction Limits")
    ax.plot(x2, y2 + pi, "--", color="0.5")

    # Borders
    ax.spines["top"].set_color("0.5")
    ax.spines["bottom"].set_color("0.5")
    ax.spines["left"].set_color("0.5")
    ax.spines["right"].set_color("0.5")
    ax.get_xaxis().set_tick_params(direction="in")
    ax.get_yaxis().set_tick_params(direction="in")
    ax.xaxis.tick_bottom()
    ax.yaxis.tick_left()
    ax.tick_params(axis='both', which='major', labelsize=FONT_PARAMS['size'])

    # Labels
    # plt.title("Fit Plot for Weight", fontsize="18", fontweight="bold", family=FONT_PARAMS['family'])
    plt.xlabel(x_label, fontsize=FONT_PARAMS['size'] + 2, family=FONT_PARAMS['family'])
    plt.ylabel(y_label, fontsize=FONT_PARAMS['size'] + 2, family=FONT_PARAMS['family'])
    plt.xlim(np.min(x) - 1, np.max(x) + 1)

    # Custom legend
    handles, labels = ax.get_legend_handles_labels()
    display = (0, 1)
    anyArtist = plt.Line2D((0, 1), (0, 0), color=FILL_COLOR)  # create custom artists
    legend = plt.legend(
        [handle for i, handle in enumerate(handles) if i in display] + [anyArtist],
        [label for i, label in enumerate(labels) if i in display] + ["95% Confidence Limits"],
        loc=9, bbox_to_anchor=(0, -0.21, 1., 0.102), ncol=3, mode="expand", fontsize=16
    )
    legend.get_frame().set_edgecolor("0.5")

    # Save Figure
    plt.tight_layout()


FONT_PARAMS = {
    'size': 18,
    'family': 'Times New Roman',
}

# FILL_COLOR = '#b9cfe7'
# FILL_COLOR = '#e0e0e0'
FILL_COLOR = '#ebd8d8'

if __name__ == '__main__':
    mpl.rc('font', family='Times New Roman')
    directory = "c:/Users/Sergii/Dell_D/MyPapers/Paper_ISR_QuietConditions/Data/"
    file = "LSTID_1.txt"
    file_name = f"{directory}{file}"
    with open(file_name, 'r') as f:
        columns = f.readline().strip('\n').split('\t')
        old_raw_data = f.readlines()
        raw_data = []
    for line in old_raw_data:
        new_line = re.sub(r'\s+', r'\t', line)
        raw_data.append(new_line)
    split_data = [x.strip('\n').replace(',', '.').split('\t') for x in raw_data]
    data = list(zip(*split_data))
    number_data = []
    for datum in data:
        new_row = list(map(float, datum))
        number_data.append(new_row)
    var = {}
    for i in range(len(columns)):
        var[columns[i]] = number_data[i]
    print(stats.pearsonr(var['F30'], var['h']))
    x = np.array(var['F30'])
    y = np.array(var['T'])
    plot_stat_params(x, y)
    plt.show()