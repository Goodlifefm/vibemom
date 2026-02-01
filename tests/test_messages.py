from src.bot.messages import COPY_IDS, get_copy


def test_all_copy_ids_resolvable():
    for copy_id in COPY_IDS:
        text = get_copy(copy_id)
        assert isinstance(text, str), f"{copy_id} should return str"
        assert len(text) >= 0, f"{copy_id} may be empty but must be str"
