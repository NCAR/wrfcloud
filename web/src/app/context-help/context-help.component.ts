import {Component, Inject} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";
import {HelpEntry, helpData} from "./help-data";
import {AppComponent} from "../app.component";


@Component({
    selector: 'app-context-help',
    templateUrl: './context-help.component.html',
    styleUrls: ['./context-help.component.sass']
})
export class ContextHelpComponent
{
    /**
     * Reference to the application singleton
     */
    public app: AppComponent;


    /**
     * Display this help entry
     */
    public entry: HelpEntry;


    /**
     * Get the help entry to display
     *
     * @param dialogRef
     * @param data
     */
    constructor(public dialogRef: MatDialogRef<ContextHelpComponent>, @Inject(MAT_DIALOG_DATA) public data: string)
    {
        this.app = AppComponent.singleton;
        this.entry = this.findHelpEntry(data);
    }


    /**
     * Find a help entry in the data
     * @param id Search for this Help ID
     */
    private findHelpEntry(id: string): HelpEntry
    {
        for (let entry of helpData)
            if (entry.id === id)
                return entry;

        return {
            'id': id,
            'title': 'Not Found',
            'text': [
                'The help for this text ID was not found: ' + id + '.'
            ]
        };
    }
}
