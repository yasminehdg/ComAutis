from django.contrib import admin
from django.utils.html import format_html
from .models import Topic, Post

class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'icon_img', 'created_at')
    search_fields = ('title', 'created_by__username')
    list_filter = ('icon', 'created_at')

    def icon_img(self, obj):
        if obj.icon:
            return format_html(
                '<img src="/static/forum/icons/{}.png" style="width:30px;height:30px;" />', obj.icon
            )
        return "-"
    icon_img.short_description = 'Icône'

class PostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'created_by', 'created_at')
    search_fields = ('topic__title', 'created_by__username')
    list_filter = ('created_at',)

admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
