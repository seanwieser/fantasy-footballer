"Module containing all pages within the Stats Center."

from backend.db import DbManager
from frontend.utils import common_header, table
from nicegui import ui

# Color scheme
PRIMARY_COLOR = '#2563eb'
SECONDARY_COLOR = '#f8fafc'


@ui.page('/stats_center')
def page():
    common_header()

    # Hero section
    with ui.column().classes('w-full items-center px-8 py-16 bg-gradient-to-br from-blue-50 to-indigo-100'):
        with ui.column().classes('max-w-4xl text-center gap-6'):
            ui.label('Welcome to Stats Center').classes('text-5xl font-bold text-gray-800')
            ui.label('Your centralized platform for data analytics, insights, and statistical analysis').classes(
                'text-xl text-gray-600')
            ui.button('Get Started', on_click=lambda: ui.notify('Getting started...')).props(
                'unelevated size=lg').classes('mt-4')

    # Main content - Stats cards
    with ui.column().classes('w-full items-center px-8 py-16 bg-white'):
        with ui.column().classes('max-w-7xl w-full gap-8'):
            ui.label('Explore Our Tools').classes('text-3xl font-bold text-gray-800 mb-4')

            # Grid of stat cards
            with ui.grid(columns=3).classes('w-full gap-6'):
                # Card 1: Analytics Dashboard
                with ui.card().classes('p-6 hover:shadow-lg transition-shadow cursor-pointer'):
                    ui.icon('analytics', size='3rem').classes('text-blue-600 mb-4')
                    ui.label('Analytics Dashboard').classes('text-xl font-semibold mb-2')
                    ui.label('View comprehensive analytics and real-time metrics for your data').classes(
                        'text-gray-600 mb-4')
                    ui.button('Explore', on_click=lambda: ui.navigate.to('/stats_center/analytics')).props('flat color=primary')

                # Card 2: Reports
                with ui.card().classes('p-6 hover:shadow-lg transition-shadow cursor-pointer'):
                    ui.icon('assessment', size='3rem').classes('text-green-600 mb-4')
                    ui.label('Reports').classes('text-xl font-semibold mb-2')
                    ui.label('Generate detailed reports and export your statistical analysis').classes(
                        'text-gray-600 mb-4')
                    ui.button('Explore', on_click=lambda: ui.navigate.to('/stats_center/reports')).props('flat color=primary')

                # Card 3: Data Visualization
                with ui.card().classes('p-6 hover:shadow-lg transition-shadow cursor-pointer'):
                    ui.icon('bar_chart', size='3rem').classes('text-purple-600 mb-4')
                    ui.label('Data Visualization').classes('text-xl font-semibold mb-2')
                    ui.label('Create stunning visualizations from your datasets').classes('text-gray-600 mb-4')
                    ui.button('Explore', on_click=lambda: ui.navigate.to('/stats_center/visualization')).props('flat color=primary')

                # Card 4: Statistical Tests
                with ui.card().classes('p-6 hover:shadow-lg transition-shadow cursor-pointer'):
                    ui.icon('calculate', size='3rem').classes('text-orange-600 mb-4')
                    ui.label('Statistical Tests').classes('text-xl font-semibold mb-2')
                    ui.label('Run hypothesis tests and statistical computations').classes('text-gray-600 mb-4')
                    ui.button('Explore', on_click=lambda: ui.navigate.to('/stats_center/tests')).props('flat color=primary')

                # Card 5: Data Import
                with ui.card().classes('p-6 hover:shadow-lg transition-shadow cursor-pointer'):
                    ui.icon('cloud_upload', size='3rem').classes('text-cyan-600 mb-4')
                    ui.label('Data Import').classes('text-xl font-semibold mb-2')
                    ui.label('Upload and manage your datasets from various sources').classes('text-gray-600 mb-4')
                    ui.button('Explore', on_click=lambda: ui.navigate.to('/stats_center/import')).props('flat color=primary')

                # Card 6: Settings
                with ui.card().classes('p-6 hover:shadow-lg transition-shadow cursor-pointer'):
                    ui.icon('settings', size='3rem').classes('text-gray-600 mb-4')
                    ui.label('Settings').classes('text-xl font-semibold mb-2')
                    ui.label('Configure your preferences and manage your account').classes('text-gray-600 mb-4')
                    ui.button('Explore', on_click=lambda: ui.navigate.to('/stats_center/settings')).props('flat color=primary')

    # Footer
    with ui.footer().classes('bg-gray-800 text-white'):
        with ui.column().classes('w-full items-center px-8 py-8'):
            with ui.row().classes('max-w-7xl w-full justify-between'):
                ui.label('© 2025 Stats Center. All rights reserved.').classes('text-gray-400')
                with ui.row().classes('gap-6'):
                    ui.link('About', '/about').classes('text-gray-400 hover:text-white')
                    ui.link('Contact', '/contact').classes('text-gray-400 hover:text-white')
                    ui.link('Privacy', '/privacy').classes('text-gray-400 hover:text-white')


# Placeholder pages
@ui.page('/stats_center/analytics')
def analytics():
    ui.label('Analytics Dashboard - Coming Soon').classes('text-2xl font-bold p-8')
    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).props('flat')


@ui.page('/stats_center/reports')
def reports():
    ui.label('Reports - Coming Soon').classes('text-2xl font-bold p-8')
    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).props('flat')


@ui.page('/stats_center/visualization')
def visualization():
    ui.label('Data Visualization - Coming Soon').classes('text-2xl font-bold p-8')
    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).props('flat')


@ui.page('/stats_center/tests')
def tests():
    ui.label('Statistical Tests - Coming Soon').classes('text-2xl font-bold p-8')
    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).props('flat')


@ui.page('/stats_center/import')
def import_data():
    ui.label('Data Import - Coming Soon').classes('text-2xl font-bold p-8')
    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).props('flat')


@ui.page('/stats_center/settings')
def settings():
    ui.label('Settings - Coming Soon').classes('text-2xl font-bold p-8')
    ui.button('← Back to Home', on_click=lambda: ui.navigate.to('/')).props('flat')
