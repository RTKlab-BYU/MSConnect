from django.urls import path, include
from . import views
from django.conf.urls.static import static
from . import views
from django.conf import settings


urlpatterns = [
    path('', views.dashboard, name='index'),
    path("uploadraw/", views.uploadraw, name='uploadraw'),
    path("results/", views.results, name='results'),
    path('api/auth/', views.auth, name="auth"),
    path("process/", views.process, name='process'),
    path("maxquant/", views.maxquant, name='maxquant'),
    path("msfragger/", views.msfragger, name='msfragger'),
    path("pd/", views.pd, name='Protein Discoverer'),

    path("help/", views.help, name='help'),
    path("settings/", views.settings_page, name='Settings'),
    path("maxquant/load/<int:pk>", views.maxquant_plot, name='maxquant_plot'),



    path("results/load/<int:pk>", views.load_results, name='load_result'),
    path('api/', views.FileList.as_view()),
    path('api/<int:pk>/', views.FileDetail.as_view()),
    path('api/spectrominequeue/', views.SpectromineQueueList.as_view()),
    path('api/spectrominequeue/<int:pk>/',
         views.SpectromineQueueDetail.as_view()),
    path('api/spectromineworker/', views.SpectromineWorkerList.as_view()),
    path('api/spectromineworker/<int:pk>/',
         views.SpectromineWorkerDetail.as_view()),
    path('api/maxquantqueue/', views.MaxquantQueueList.as_view()),
    path('api/maxquantqueue/<int:pk>/',
         views.MaxquantQueueDetail.as_view()),
    path('api/maxquantworker/', views.MaxquantWorkerList.as_view()),
    path('api/maxquantworker/<int:pk>/', views.MaxquantWorkerDetail.as_view()),
    path('api/msfraggerqueue/', views.MsfraggerQueueList.as_view()),
    path('api/msfraggerqueue/<int:pk>/',
         views.MsfraggerQueueDetail.as_view()),
    path('api/msfraggerworker/', views.MsfraggerWorkerList.as_view()),
    path('api/msfraggerworker/<int:pk>/',
         views.MsfraggerWorkerDetail.as_view()),
    path('api/pdqueue/', views.PdQueueList.as_view()),
    path('api/pdqueue/<int:pk>/',
         views.PdQueueDetail.as_view()),
    path('api/pdworker/', views.PdWorkerList.as_view()),
    path('api/pdworker/<int:pk>/',
         views.PdWorkerDetail.as_view()),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
