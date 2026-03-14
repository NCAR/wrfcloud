import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";

@Component({
    selector: 'app-error-dialog',
    templateUrl: './error-dialog.html',
    styleUrls: ['./error-dialog.sass'],
    standalone: false
})
export class ErrorDialogComponent implements OnInit
{
  constructor(public dialogRef: MatDialogRef<ErrorDialogComponent>, @Inject(MAT_DIALOG_DATA) public data: Array<string>)
  {
  }


  ngOnInit(): void
  {
  }
}
