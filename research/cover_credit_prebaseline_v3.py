"""Blind executable coverage for corrected, approved baseline design."""
import cover_credit_prebaseline_candidate as collector
import count_credit_prebaseline_v3 as study


if __name__ == '__main__':
    collector.study.OUT=study.OUT; collector.study.SPEC=study.SPEC
    root=study.base.ROOT
    collector.symbols.g.CACHE_SOURCE=[root/'credit_prebaseline_v2_candidate'/'quote_cache',
        root/'credit_prebaseline_candidate'/'quote_cache',
        root/'credit_renewal_v2_candidate'/'quote_cache']
    collector.run()
