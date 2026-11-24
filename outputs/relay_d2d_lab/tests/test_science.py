import numpy as np
from sim.model import Config, evaluate, wilson


def test_df_and_direct_closed_forms_match_independent_sample_events():
    c=Config(samples=1000000,seed=3571)
    r=evaluate(c,[-4,0,6,12])
    for row in r['rows']:
        for mode,closed in [('DF','df_closed'),('Direct','direct_closed')]:
            p=row[closed]
            # Six standard errors avoids flaky repeated testing across grid.
            tolerance=6*np.sqrt(max(p*(1-p),1/c.samples)/c.samples)+2/c.samples
            assert abs(row['modes'][mode]['outage']-p)<tolerance


def test_variable_gain_power_and_snr_against_received_waveform():
    rng=np.random.default_rng(2903);n=500000
    h=(rng.normal(size=n)+1j*rng.normal(size=n))/np.sqrt(2)
    g=(rng.normal(size=n)+1j*rng.normal(size=n))/np.sqrt(2)
    x=np.exp(1j*(rng.integers(0,4,n)*np.pi/2))
    nr=(rng.normal(size=n)+1j*rng.normal(size=n))/np.sqrt(2)
    nd=(rng.normal(size=n)+1j*rng.normal(size=n))/np.sqrt(2)
    ps,pr=4,3
    vg=np.sqrt(pr/(ps*abs(h)**2+1))
    fg=np.sqrt(pr/(ps+1))
    for gain in [vg,fg]:
        relay=gain*(np.sqrt(ps)*h*x+nr)
        assert abs(np.mean(abs(relay)**2)-pr)/pr<.015
        signal=g*gain*np.sqrt(ps)*h*x
        noise=g*gain*nr+nd
        measured=np.mean(abs(signal)**2)/np.mean(abs(noise)**2)
        predicted=np.mean(ps*abs(h)**2*abs(g)**2*gain**2)/np.mean(abs(g)**2*gain**2+1)
        assert abs(measured-predicted)/predicted<.015


def test_reproducibility_and_selector_constraint():
    c=Config(samples=10000,seed=42)
    a=evaluate(c,[-10,0,10,20]);b=evaluate(c,[-10,0,10,20]);assert a==b
    for row in a['rows']:
        chosen=row['selected']
        feasible=[m for m in ['DF','AF-FG','AF-VG'] if row['modes'][m]['ci95'][1]<=c.qos]
        if chosen=='INFEASIBLE':assert not feasible
        else:
            assert chosen in feasible
            assert row['modes'][chosen]['bits_per_joule']==max(row['modes'][m]['bits_per_joule'] for m in feasible)


def test_zero_outage_has_positive_confidence_upper_bound():
    lo,hi=wilson(0,1000000)
    assert abs(lo)<1e-15 and 0<hi<.000004
