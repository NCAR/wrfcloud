export interface HelpEntry
{
    id: string;
    title: string;
    text: Array<string>;
}


export const helpData: Array<HelpEntry> = [
    {
        'id': 'app-about',
        'title': 'WRF Cloud',
        'text': [
            'WRF Cloud is open source software developed at <a href="https://ncar.ucar.edu" target="_blank">NCAR</a>.',
            'Visit our <a href="https://www.wrfcloud.com" target="_blank">website</a> or <a href="https://wrfcloud.readthedocs.io/en/stable/" target="_blank">user guide</a> for more information.'
        ]
    },

    {
        'id': 'prefs-user-info',
        'title': 'User Information',
        'text': [
            'This is intended for informational purposes only and is read-only.',
            'If you have an administrator role, you can edit this information (and the information of other users) on the Manage Users tab.'
        ]
    }
];
