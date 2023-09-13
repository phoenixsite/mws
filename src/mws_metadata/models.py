from djongo import models

class StoreMetadata(models.Model):

    _id = models.ObjectIdField()

    class ColorTheme(models.TextChoices):
        PURPLE = "purple", "Purple"
        RED = "red", "Red"
        BLUE = "blue", "Blue"
        YELLOW = "yellow", "Yellow"
    
    main_theme_color = models.CharField(
        max_length=10,
        choices=ColorTheme.choices,
        default=ColorTheme.PURPLE,
        help_text="Please pick a color for the main theme."
    )

    # First column
    footer_col1_title = models.CharField(
        "title of the first footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col1_row1_text = models.CharField(
        "text of the first row of the first footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col1_row1_url = models.URLField(
        "url of the first row of first footer column",
        blank=True,
        null=True,
    )

    footer_col1_row2_text = models.CharField(
        "text of the second row of the first footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col1_row2_url = models.URLField(
        "url of the second row of first footer column",
        blank=True,
        null=True,
    )

    footer_col1_row3_text = models.CharField(
        "text of the third row of the first footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col1_row3_url = models.URLField(
        "url of the third row of first footer column",
        blank=True,
        null=True,
    )

    footer_col1_row4_text = models.CharField(
        "text of the fourth row of the first footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col1_row4_url = models.URLField(
        "url of the fourth row of first footer column",
        blank=True,
        null=True,
    )

    footer_col1_row5_text = models.CharField(
        "text of the fifth row of the first footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col1_row5_url = models.URLField(
        "url of the fifth row of first footer column",
        blank=True,
        null=True,
    )


    # Second column
    footer_col2_title = models.CharField(
        "title of the second footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col2_row1_text = models.CharField(
        "text of the first row of the second footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col2_row1_url = models.URLField(
        "url of the first row of second footer column",
        blank=True,
        null=True,
    )

    footer_col2_row2_text = models.CharField(
        "text of the second row of the second footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col2_row2_url = models.URLField(
        "url of the second row of second footer column",
        blank=True,
        null=True,
    )

    footer_col2_row3_text = models.CharField(
        "text of the third row of the second footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col2_row3_url = models.URLField(
        "url of the third row of second footer column",
        blank=True,
        null=True,
    )

    footer_col2_row4_text = models.CharField(
        "text of the fourth row of the second footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col2_row4_url = models.URLField(
        "url of the fourth row of second footer column",
        blank=True,
        null=True,
    )

    footer_col2_row5_text = models.CharField(
        "text of the fifth row of the second footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col2_row5_url = models.URLField(
        "url of the fifth row of second footer column",
        blank=True,
        null=True,
    )


    # Third column
    footer_col3_title = models.CharField(
        "title of the first footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col3_row1_text = models.CharField(
        "text of the first row of the third footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col3_row1_url = models.URLField(
        "url of the first row of third footer column",
        blank=True,
        null=True,
    )

    footer_col3_row2_text = models.CharField(
        "text of the second row of the third footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col3_row2_url = models.URLField(
        "url of the second row of third footer column",
        blank=True,
        null=True,
    )

    footer_col3_row3_text = models.CharField(
        "text of the third row of the third footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col3_row3_url = models.URLField(
        "url of the third row of third footer column",
        blank=True,
        null=True,
    )

    footer_col3_row4_text = models.CharField(
        "text of the fourth row of the third footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col3_row4_url = models.URLField(
        "url of the fourth row of third footer column",
        blank=True,
        null=True,
    )

    footer_col3_row5_text = models.CharField(
        "text of the fifth row of the third footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col3_row5_url = models.URLField(
        "url of the fifth row of third footer column",
        blank=True,
        null=True,
    )


    # Fourth column
    footer_col4_title = models.CharField(
        "title of the fourth footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col4_row1_text = models.CharField(
        "text of the first row of the fourth footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col4_row1_url = models.URLField(
        "url of the first row of fourth footer column",
        blank=True,
        null=True,
    )

    footer_col4_row2_text = models.CharField(
        "text of the second row of the fourth footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col4_row2_url = models.URLField(
        "url of the second row of fourth footer column",
        blank=True,
        null=True,
    )

    footer_col4_row3_text = models.CharField(
        "text of the third row of the fourth footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col4_row3_url = models.URLField(
        "url of the third row of fourth footer column",
        blank=True,
        null=True,
    )

    footer_col4_row4_text = models.CharField(
        "text of the fourth row of the fourth footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col4_row4_url = models.URLField(
        "url of the fourth row of fourth footer column",
        blank=True,
        null=True,
    )

    footer_col4_row5_text = models.CharField(
        "text of the fifth row of the fourth footer column",
        max_length=50,
        blank=True,
        null=True,
    )

    footer_col4_row5_url = models.URLField(
        "url of the fifth row of fourth footer column",
        blank=True,
        null=True,
    )

    def _get_column(self, ncol):
        """
        Return the texts and urls in the column 'ncol'.
        """

        COLS = [
            [
                (self.footer_col1_row1_text,
                 self.footer_col1_row1_url),
                
                (self.footer_col1_row2_text,
                 self.footer_col1_row2_url),
                
                (self.footer_col1_row3_text,
                 self.footer_col1_row3_url),
                
                (self.footer_col1_row4_text,
                 self.footer_col1_row4_url),
                
                (self.footer_col1_row5_text,
                 self.footer_col1_row5_url),
            ],
            [
                (self.footer_col2_row1_text,
                 self.footer_col2_row1_url),
                
                (self.footer_col2_row2_text,
                 self.footer_col2_row2_url),
                
                (self.footer_col2_row3_text,
                 self.footer_col2_row3_url),
                
                (self.footer_col2_row4_text,
                 self.footer_col2_row4_url),
                
                (self.footer_col2_row5_text,
                 self.footer_col2_row5_url),
            ],
            [
                (self.footer_col3_row1_text,
                 self.footer_col3_row1_url),
                
                (self.footer_col3_row2_text,
                 self.footer_col3_row2_url),
                
                (self.footer_col3_row3_text,
                 self.footer_col3_row3_url),
                
                (self.footer_col3_row4_text,
                 self.footer_col3_row4_url),
                
                (self.footer_col3_row5_text,
                 self.footer_col3_row5_url),
            ],
            [
                (self.footer_col4_row1_text,
                 self.footer_col4_row1_url),
                
                (self.footer_col4_row2_text,
                 self.footer_col4_row2_url),
                
                (self.footer_col4_row3_text,
                 self.footer_col4_row3_url),
                
                (self.footer_col4_row4_text,
                 self.footer_col4_row4_url),
                
                (self.footer_col4_row5_text,
                 self.footer_col4_row5_url),
            ],
        ]

        if ncol not in range(len(COLS)):
            return None

        return COLS[ncol]

    def _has_footer_col(self, ncol):
        """
        Check if there are any non-null or non-empty text items in the
        column 'ncol'.
        """
        
        col = self._get_column(ncol)
        return any([row[0] for row in col])

    def has_footer_col1(self):
        return self._has_footer_col(0)

    def has_footer_col2(self):
        return self._has_footer_col(1)

    def has_footer_col3(self):
        return self._has_footer_col(2)

    def has_footer_col4(self):
        return self._has_footer_col(3)

    def _col(self, ncol):
        """Return the non-null or non-empty items of column 'ncol'."""
        col = self._get_column(ncol)
        return [row for row in col if row[0]]

    def col1(self):
        return self._col(0)
    
    def col2(self):
        return self._col(1)

    def col3(self):
        return self._col(2)

    def col4(self):
        return self._col(3)

    def _get_title(self, ncol):
        """Return the title of the column 'ncol'."""
        TITLES = [
            self.footer_col1_title,
            self.footer_col2_title,
            self.footer_col3_title,
            self.footer_col4_title,
        ]

        if ncol not in range(len(TITLES)):
            return None
        return TITLES[ncol]

    def title1(self):
        return self._get_title(0)

    def title2(self):
        return self._get_title(1)

    def title3(self):
        return self._get_title(2)

    def title4(self):
        return self._get_title(3)
