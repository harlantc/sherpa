#
#  Copyright (C) 2015, 2016, 2018, 2021, 2022, 2023
#  Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# break out some of the I/O tests in the UI layer into a separate set
# of tests, in part to reduce file size, but also because some of these
# may be better placed in tests of the sherpa.astro.io module, once that
# becomes possible

import pytest

from sherpa.utils.testing import requires_data, requires_fits
from sherpa.astro import ui
from sherpa.astro.data import DataPHA
from sherpa.astro.instrument import ARF1D, RMF1D


FILE_NAME = 'acisf01575_001N001_r0085_pha3.fits'


def validate_pha(idval):
    """Check that the PHA dataset in id=idval is
    as expected.
    """

    assert ui.list_data_ids() == [idval]

    pha = ui.get_data(idval)
    assert isinstance(pha, DataPHA)

    arf = ui.get_arf(idval)
    assert isinstance(arf, ARF1D)

    rmf = ui.get_rmf(idval)
    assert isinstance(rmf, RMF1D)

    bpha = ui.get_bkg(idval, bkg_id=1)
    assert isinstance(bpha, DataPHA)

    barf = ui.get_arf(idval, bkg_id=1)
    assert isinstance(barf, ARF1D)

    brmf = ui.get_rmf(idval, bkg_id=1)
    assert isinstance(brmf, RMF1D)

    # normally the background data set would have a different name,
    # but this is a  PHA Type 3 file.
    # assert pha.name == bpha.name
    assert arf.name == barf.name
    assert rmf.name == brmf.name


@requires_fits
@requires_data
def test_pha3_read_explicit(make_data_path, clean_astro_ui):
    """Include .gz in the file name"""

    fname = make_data_path(FILE_NAME + '.gz')
    idval = 12
    ui.load_pha(idval, fname)

    validate_pha(idval)

    # TODO: does this indicate that the file name, as read in,
    #       should have the .gz added to it to match the data
    #       read in, or left as is?
    pha = ui.get_data(idval)
    bpha = ui.get_bkg(idval, bkg_id=1)
    assert pha.name == bpha.name + '.gz'
    assert pha.name == fname


@requires_fits
@requires_data
def test_pha3_read_implicit(make_data_path, clean_astro_ui):
    """Exclude .gz from the file name"""

    idval = "13"
    fname = make_data_path(FILE_NAME)
    ui.load_pha(idval, fname)

    validate_pha(idval)

    pha = ui.get_data(idval)
    bpha = ui.get_bkg(idval, bkg_id=1)
    assert pha.name == bpha.name
    assert pha.name == fname


@requires_fits
@requires_data
def test_hrci_imaging_mode_spectrum(make_data_path, clean_astro_ui):
    """This is a follow-on test based on issue #1830"""

    from sherpa.astro import io
    if io.backend.__name__ == "sherpa.astro.io.pyfits_backend":
        pytest.xfail()  # issue #1830

    infile = make_data_path("chandra_hrci/hrcf24564_000N030_r0001" +
                            "_pha3.fits.gz")
    ui.load_pha(infile)

    # Just check we can evaluate the model folding through the
    # response, and compare to the data. Getting a "nice" fit
    # is surprisingly hard so do a non-physical fit.
    #
    ui.notice(4, 6)
    pl = ui.create_model_component("powlaw1d", "pl")
    pl.gamma = 2.24
    pl.ampl = 4.6e-3
    ui.set_source(ui.powlaw1d.pl)

    ui.set_stat("chi2gehrels")

    # regression tests (the expected values were calculated using CIAO
    # 4.15/crates).
    #
    assert ui.calc_stat() == pytest.approx(39.58460766890158)

    ui.subtract()
    assert ui.calc_stat() == pytest.approx(39.611346193696164)
