"""List items, tokens, types and whether they're equippable or usable.

Usage: PYTHONPATH=src python3 scripts/list_items.py
"""
from jedi_fugitive.items import consumables, weapons, armor

def main():
    print("Consumable ITEM_DEFS:")
    for it in getattr(consumables, 'ITEM_DEFS', []):
        print(f"- id: {it.get('id')!s:20} token: {it.get('token')!s:3} type: {it.get('type')!s:12} name: {it.get('name')!s:30} desc: {it.get('description','(no desc)')}")
    print()

    print("Weapon prototypes (WEAPONS):")
    for w in getattr(weapons, 'WEAPONS', []):
        name = getattr(w, 'name', str(w))
        desc = getattr(w, 'description', '')
        print(f"- name: {name!s:30} type: {getattr(w,'weapon_type',None)} desc: {desc}")
    print()

    print("Armors (ARMORS):")
    for a in getattr(armor, 'ARMORS', []):
        name = getattr(a, 'name', str(a))
        desc = getattr(a, 'description', '')
        slot = getattr(a, 'slot', 'body')
        print(f"- name: {name!s:30} slot: {slot!s:6} desc: {desc}")
    print()

    # tokens used by map_features as defaults
    print("Default map tokens and token map used by equipment:")
    try:
        from jedi_fugitive.items.tokens import TOKEN_MAP
        token_map = {k: v for k, v in TOKEN_MAP.items()}
    except Exception:
        token_map = { 'v': {'name':'Vibroblade'}, 's': {'name':'Energy Shield'}, 'b': {'name':'Blaster Pistol'} }
        # augment with consumables
        for it in getattr(consumables, 'ITEM_DEFS', []):
            tk = it.get('token')
            if tk:
                token_map.setdefault(tk, {'name': it.get('name'), 'description': it.get('description')})

    for k, v in token_map.items():
        name = v.get('name') if isinstance(v, dict) else str(v)
        desc = v.get('description') if isinstance(v, dict) else None
        print(f"- token: {k!s:3} -> {name!s:30} desc: {desc or '(none)'}")

    # quick classification: which tokens are equippable vs only usable
    print()
    print("Classification: equippable vs usable-only:")
    equippable_tokens = set(['v','b','s'])
    usable_tokens = set([it.get('token') for it in getattr(consumables, 'ITEM_DEFS', []) if it.get('token')])
    for tk in sorted(set(list(equippable_tokens) + list(usable_tokens))):
        is_equip = 'Yes' if tk in equippable_tokens else 'No'
        is_usable = 'Yes' if tk in usable_tokens else 'No'
        print(f"- token: {tk!s:3} equippable: {is_equip:3} usable: {is_usable:3}")

if __name__ == '__main__':
    main()
