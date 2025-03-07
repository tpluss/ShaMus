from django import forms
from django.core.exceptions import ValidationError
from .models import Artist, Album, Track


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        self.allowed_extensions = kwargs.pop('allowed_ext', [])
        kwargs.setdefault('widget', MultipleFileInput(
            attrs={'accept': ', '.join(self.allowed_extensions),
                   'multiple': 'multiple'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        
        def single_ext_clean(f):
            is_clean = False
            for ext in self.allowed_extensions:
                if f._name.endswith(ext):
                    is_clean = True
                    break

            if not is_clean:
                raise forms.ValidationError(
                    f'Только {",".join(self.allowed_extensions)}')

        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
            [single_ext_clean(d) for d in data]
        else:
            result = [single_file_clean(data, initial)]
            single_ext_clean(data)

        return result


class UploadFileForm(forms.Form):
    file_field = MultipleFileField(label='Выберите файлы',
                                   allowed_ext=('mp3', ))


class AddArtistForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ['title']

    def __init__(self, *args, **kwargs):
        self.is_title_repeat_allowed = kwargs.pop('is_title_repeat_allowed',
                                                  False)

        super().__init__(*args, **kwargs)

    def clean(self):
        cd = self.cleaned_data

        if 'title' in cd:
            cd['title'] = cd['title'].strip()

            if not self.is_title_repeat_allowed:
                is_repeated = (Artist.used.filter(title__iexact=cd['title'])
                               .count() > 0)

                if is_repeated:
                    raise ValidationError({
                        'title': ValidationError("Исполнитель с таким именем "
                                                 "сушествует.", code="repeat")})

        return cd


class AddAlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['artist', 'year', 'title', 'track_order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['artist'].widget.attrs['class'] = 'sfqs'
        self.fields['title'].widget.attrs['size'] = '200'
        self.fields['track_order'].widget.attrs['cols'] = '75'
        self.fields['track_order'].widget.attrs['rows'] = '3'


class AddTrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = ['title', 'duration', 'artist']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
      
        self.fields['artist'].queryset = kwargs['initial']['artist']
        self.fields['artist'].widget.attrs['class'] = 'sfqs'
        self.fields['title'].widget.attrs['size'] = '200'
        self.fields['duration'].widget.attrs['size'] = '5'
