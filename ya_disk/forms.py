from django import forms


class PublicKeyForm(forms.Form):
    """
    Форма для ввода публичной ссылки (public_key).
    """
    public_url = forms.URLField(
        label="Public URL",
        required=True,
        widget=forms.URLInput(attrs={"placeholder": "Введите публичную ссылку"})
    )
