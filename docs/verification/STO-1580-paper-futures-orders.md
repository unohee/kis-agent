# STO-1580 paper futures order verification

## Environment and result

Live KIS paper calls were unavailable in this worktree because no `KIS_APP_KEY`,
`KIS_APP_SECRET`, or paper account number was present. No `rt_cd=0` result is
claimed. The credential-safe test intercepts HTTP after KIS TR-ID conversion and
verifies the complete JSON body and final TR ID for all four paths with
`KIS_PAPER=1` and `KIS_ACCOUNT_CODE=03`:

| Path | Expected paper TR_ID | Offline result |
| --- | --- | --- |
| buy | `VTTO1101U` | request body and final TR_ID verified |
| sell | `VTTO1101U` | request body and final TR_ID verified |
| amend | `VTTO1103U` | request body and final TR_ID verified |
| cancel | `VTTO1103U` | request body and final TR_ID verified |

Run `python -m pytest tests/unit/test_futures_order_api.py::test_paper_daytime_four_paths_resolve_final_tr_ids -q --no-cov`.
The response contract is independently sourced from the official KIS
`open-trading-api` `chk_order.py` and `chk_order_rvsecncl.py` `COLUMN_MAPPING`
dictionaries; tests compare those field sets with this package's TypedDicts.
For live verification, export paper credentials plus `KIS_PAPER=1` and
`KIS_ACCOUNT_CODE=03`, submit buy and sell during the daytime session, then amend
and cancel the returned order numbers; record `rt_cd`, `msg_cd`, and `ODNO` for
each call. Night TR IDs require a real account and are outside paper support.