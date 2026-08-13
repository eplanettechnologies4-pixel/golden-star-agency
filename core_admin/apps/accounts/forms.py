from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomerSignupForm(forms.ModelForm):
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Enter first name'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Enter last name'
    }))
    phone = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Enter phone number'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Enter password'
    }))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Confirm password'
    }))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
                'placeholder': 'Enter email address'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        if User.objects.filter(username=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        user.role = 'customer'
        user.is_email_verified = False  # requires verification
        if commit:
            user.save()
        return user



class AgentSignupForm(forms.ModelForm):
    full_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Enter full name'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Enter password'
    }))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Confirm password'
    }))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Office / Physical Address (Optional)'
    }))
    profile_photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-brand-orange/10 file:text-brand-orange hover:file:bg-brand-orange/20',
        'accept': 'image/*'
    }))
    id_card_front = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-brand-orange/10 file:text-brand-orange hover:file:bg-brand-orange/20',
        'accept': 'image/*'
    }))
    id_card_back = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-brand-orange/10 file:text-brand-orange hover:file:bg-brand-orange/20',
        'accept': 'image/*'
    }))

    class Meta:
        model = User
        fields = ['email', 'phone', 'company_name', 'address', 'profile_photo', 'id_card_front', 'id_card_back']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
                'placeholder': 'Email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
                'placeholder': 'Phone / WhatsApp number'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
                'placeholder': 'Travel Agency Company Name'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        if User.objects.filter(username=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '').strip()
        if full_name:
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
        
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        user.role = 'agent'
        user.is_email_verified = False  # Agents must verify email first
        user.approval_status = 'pending'
        if 'address' in self.cleaned_data and self.cleaned_data['address']:
            user.address = self.cleaned_data['address']
        if 'profile_photo' in self.cleaned_data and self.cleaned_data['profile_photo']:
            user.profile_photo = self.cleaned_data['profile_photo']
        if 'id_card_front' in self.cleaned_data and self.cleaned_data['id_card_front']:
            user.id_card_front = self.cleaned_data['id_card_front']
        if 'id_card_back' in self.cleaned_data and self.cleaned_data['id_card_back']:
            user.id_card_back = self.cleaned_data['id_card_back']

        if commit:
            user.save()
        return user


class AgentDocumentsForm(forms.ModelForm):
    address = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 focus:outline-none focus:border-brand-orange',
        'placeholder': 'Enter physical address'
    }))

    class Meta:
        model = User
        fields = ['address', 'profile_photo', 'id_card_front', 'id_card_back']
        widgets = {
            'profile_photo': forms.FileInput(attrs={'class': 'w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-brand-orange/10 file:text-brand-orange hover:file:bg-brand-orange/20'}),
            'id_card_front': forms.FileInput(attrs={'class': 'w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-brand-orange/10 file:text-brand-orange hover:file:bg-brand-orange/20'}),
            'id_card_back': forms.FileInput(attrs={'class': 'w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-brand-orange/10 file:text-brand-orange hover:file:bg-brand-orange/20'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        profile = cleaned_data.get('profile_photo')
        front = cleaned_data.get('id_card_front')
        back = cleaned_data.get('id_card_back')
        
        if not self.instance.profile_photo and not profile:
            self.add_error('profile_photo', "Profile photo is required.")
        if not self.instance.id_card_front and not front:
            self.add_error('id_card_front', "ID card front image is required.")
        if not self.instance.id_card_back and not back:
            self.add_error('id_card_back', "ID card back image is required.")
            
        return cleaned_data
