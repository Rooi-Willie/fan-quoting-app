import importlib


def test_prune_legacy_flat_keys_removes_expected():
    common = importlib.import_module('pages.common')
    sample = {
        'fan_config_id': 1,
        'fan_uid': 'F-123',
        'fan_hub': 500,
        'blade_sets': '6',
        'selected_components_unordered': ['casing'],
        'component_details': {'casing': {'Material Thickness': 5}},
        'markup_override': 1.4,
        'motor_price_after_markup': 900,
        'motor_markup_override': 1.2,
        'quote_ref': 'OLDREF',
        'buy_out_items_list': [],
        'server_summary': {'final_price': 123},
        'meta': {'version': 2},
        'fan': {'config_id': 1, 'uid': 'F-123'},
        'components': {'selected': ['casing'], 'by_name': {}},
        'calculation': {}
    }
    pruned = common.prune_legacy_flat_keys(sample)
    removed_keys = [
        'fan_config_id','fan_uid','fan_hub','blade_sets','selected_components_unordered','component_details',
        'markup_override','motor_price_after_markup','motor_markup_override','quote_ref','buy_out_items_list','server_summary'
    ]
    for k in removed_keys:
        assert k not in pruned
