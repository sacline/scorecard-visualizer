"""Interface for plotting College Scorecard data.

The interface features a MainWindow containing a Matplotlib Figure where the
data can be plotted. The MainWindow's menu allows the user to open a
PlotConfigWindow where they can select the data to be plotted. The selection
interface is organized with SeriesOptions objects, which contain drop down
boxes for users to easily select the college, type of data, and year range they
want to plot.

The interface is organized by using an Interface class that contains an
instance of each Class used in the interface. Communication between each of the
classes is possible through the Interface. Each part of the interface contains
a reference to a parent object, and the top-level parent object is the
Interface.
"""
import sqlite3
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt4 import QtCore, QtGui

class Interface():
    """Top-level class that contains all other interface classes.

    The Interface class is used to communicate between different classes that
    comprise the user interface. For example, the window containing the user
    settings (plot_config_window) for the plots can trigger a database query
    from the plot_settings object because they are both members of this class.
    This class functions as the controller in a MVC design pattern.

    Attributes:
        plot_settings: Queries the database and stores Scorecard data.
        plot_config_window: Window used to specify data to be plotted.
        main: Main window of the application.
        main_menu: Menu bar for the application.
    """
    def __init__(self, db_path):
        self.plot_settings = PlotSettings(db_path)

        self.plot_config_window = PlotConfigWindow(
            self, self.plot_settings.college_names,
            self.plot_settings.year_names, self.plot_settings.data_types)

        self.main = MainWindow(self)
        self.main_menu = MainMenu(self)
        self.main.show()

class MainWindow(QtGui.QMainWindow):
    """Main window of the interface containing the other interface elements.

    Attributes:
        parent: Reference to the parent Interface object.
        rect: Dimensions of the axes objects.
        figure: Figure object that contains all axes/plots.
        canvas: FigureCanvas connecting PyQt with Matplotlib elements.
    """

    def __init__(self, parent):
        QtGui.QMainWindow.__init__(self)
        self.parent = parent

        self.figure = self.build_figure()
        self.canvas = FigureCanvas(self.figure)
        self.setCentralWidget(self.canvas)
        self.show()

    @staticmethod
    def build_figure():
        """Build the initial figure on application startup.

        Returns:
            figure: figure containing the initial axes object(s).
        """
        figure = plt.figure()
        title_text =(
            'Use the menubar above (Plot => New Plot) to plot data.')
        figure.suptitle(title_text, fontsize=14, y=0.5)
        figure.subplots_adjust(left=0.075)
        return figure

    def update_figure(self):
        """Update the figure with an Axes for each plotted dataset.

        This code is executed when the application receives a request to plot
        datasets and after the data has been retrieved from the database. Each
        plot is illustrated as a scatterplot with markers of different colors
        and shapes to differentiate between datasets. If no data exists for
        a user-requested plot, it is skipped and the user is alerted with a
        message box.
        """
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        markers = ['o', 's', '^']

        #clear the figure
        for plot in self.figure.get_axes():
            self.figure.delaxes(plot)
        self.figure.suptitle('')

        #parent axes created to share x axis with other axes
        parent_axes = self.build_parent_axes()

        #add twinned axes until number of axes equals number of series
        ax_list = [parent_axes]
        series_list = self.parent.plot_settings.get_series_plots()
        if len(series_list) > 1:
            for series in series_list[1:]:
                ax_list.append(parent_axes.twinx())

        count = 0
        for index, series in enumerate(series_list):
            x_data, y_data = series.get_xy_data()

            #skip if data does not exist
            if len(y_data) == 0 or (len(y_data) == 1 and y_data[0] is None):
                ax_list[index].set_axis_off()
                self.create_popup(
                    series.data_type + ' data does not exist for ' +
                    series.college + ' for years ' + series.start_year + '-' +
                    series.end_year + '. Data will not appear in plot.')
                continue

            #plot the data
            ax_label = series.college + ' ' + series.data_type
            color = colors[count%len(colors)]
            marker = markers[int(count/len(colors))]
            ax_list[index].scatter(
                x_data, y_data, c=color, marker=marker, label=ax_label)

            #configure the y axis
            ax_list[index].set_ylim(self.get_y_limits(y_data))
            ax_list[index].set_ylabel(series.data_type, color=color)
            ax_list[index].ticklabel_format(axis='y', useOffset=False)
            ax_list[index].tick_params(axis='y', colors=color)

            #adjust the plot for new y axes
            if count > 1:
                self.figure.subplots_adjust(right=0.9 - 0.025 * count)
                ax_list[index].spines['right'].set_position(
                    ('axes', 0.95 + .07 * count))
            count = count + 1

        #create the legend
        lines, labels = [], []
        for ax in ax_list:
            ax_lines, ax_labels = ax.get_legend_handles_labels()
            lines += ax_lines
            labels += ax_labels
        parent_axes.legend(lines, labels, loc='upper right')

    @staticmethod
    def get_y_limits(y_data):
        """Return min and max values to be used as y axis limits.

        Args:
            y_data: Data set.

        Returns:
            (y_min, y_max): Tuple with min and max axis limits.
        """
        min_scale = 0.9
        max_scale = 1.1
        clean_y_data = [y for y in y_data if y != None]
        y_min = min(clean_y_data)*min_scale
        y_max = max(clean_y_data)*max_scale
        return (y_min, y_max)

    @staticmethod
    def create_popup(string):
        """Create a simple QMessageBox with a specified message.

        This will be used to alert the user of unexpected behavior. For example,
        if the user selects data to be plotted and the query to the database
        returns no data, a popup will be created notifying the user that the
        data will not be plotted.

        Args:
            string: The message to be displayed in the message box.
        """
        msg_box = QtGui.QMessageBox()
        msg_box.setText(string)
        msg_box.exec_()

    def build_parent_axes(self):
        """Build a parent axes to hold the x axis shared by all the plots.

        Returns:
            parent_axes: Axes object with correct x axis scale.
        """
        parent_axes = plt.subplot()
        #parent_axes = self.figure.add_axes(self.rect)
        x_min = int(self.parent.plot_settings._get_year_range()[0]) - 1
        x_max = int(self.parent.plot_settings._get_year_range()[1]) + 1
        parent_axes.set_xlim([x_min, x_max])
        parent_axes.ticklabel_format(axis='x', useOffset=False)
        parent_axes.set_xticks([year for year in range(x_min, x_max+1)])
        parent_axes.set_xlabel('Year')
        return parent_axes

class MainMenu():
    """Class containing the MainWindow menu bar elements.

    Args:
        parent: The application's MainWindow object.
    """
    def __init__(self, parent):
        self.parent = parent

        filemenu = QtGui.QMenu('File', parent=self.parent.main)
        filemenu.addAction('Export Plot', self.parent.main.close)
        filemenu.addAction('Close', self.parent.main.close)
        self.parent.main.menuBar().addMenu(filemenu)

        plotmenu = QtGui.QMenu('Plot', parent=self.parent.main)
        plotmenu.addAction('New Plot', self.parent.plot_config_window.show)
        self.parent.main.menuBar().addMenu(plotmenu)

class PlotSettings():
    """Stores info for plotting Scorecard data.

    Upon starting the application, the PlotSettings object pulls the list of
    colleges, data types, and years from the database. These are used in the
    plot selection menu.

    The PlotSettings object also queries the database for each dataset the
    user wishes to plot.

    Attributes:
        college_names: List of valid college name strings.
        year_names: List of valid year strings.
        data_types: List of valid data type strings.
        series_plots: List of SeriesPlots specified by the user.
    """

    def __init__(self, db_path):
        self.cur = sqlite3.connect(db_path).cursor()

        #Data stored in PlotSettings to prevent repeated db calls.
        self.college_names = []
        self.year_names = []
        self.data_types = []

        self._get_college_names()
        self._get_year_names()
        self._get_data_types()

        self.max_college_data_index = 0
        self.series_plots = []

    def query_db(self):
        """Retrieve data from the database for each user-requested plot."""
        for series in self.series_plots:
            years = list(
                range(int(series.start_year), int(series.end_year) + 1))
            if series.is_college:
                self.cur.execute(
                    '''SELECT %s FROM College WHERE INSTNM = ?''' %
                    (series.data_type), (series.college,))
                results = self.cur.fetchall()
                if len(results) == 0:
                    print('No data found for series: ', series.to_string())
                for value in results:
                    series.data.append(value[0])
            else:
                for year in years:
                    self.cur.execute(
                        '''SELECT %s FROM "%s" JOIN College WHERE
                        "%s".college_id = College.college_id AND INSTNM = ?'''
                        % (series.data_type, year, year), (series.college,))
                    results = self.cur.fetchall()
                    if len(results) == 0:
                        print('No data found for series: ', series.to_string())
                    for value in results:
                        series.data.append(value[0])
                print(series.data)

    def add_series_plot(self, series_plot):
        """Add a SeriesPlot object to the list."""
        self.series_plots.append(series_plot)

    def clear_series_plots(self):
        """Clear the list of SeriesPlot objects."""
        self.series_plots = []

    def get_series_plots(self):
        """Returns the list of SeriesPlot objects."""
        return self.series_plots

    def _get_year_range(self):
        """Return the data's min and max years from SeriesPlot list.

        Returns:
            (min_year, max_year): Tuple containing the string
                min and max years from the dataset.
        """
        min_year = 10000
        max_year = 0
        for series in self.series_plots:
            if int(series.start_year) < min_year:
                min_year = int(series.start_year)
            if int(series.end_year) > max_year:
                max_year = int(series.end_year)
        return (str(min_year), str(max_year))

    def _get_college_names(self):
        """Retrieve names of colleges from the database and store them."""
        self.cur.execute('''
            SELECT INSTNM FROM College ORDER BY INSTNM ASC''')
        for result in self.cur.fetchall():
            self.college_names.append(result[0])

    def _get_data_types(self):
        """Retrieve data types from the databaes and store them."""
        self.cur.execute('''
            PRAGMA table_info(College)''')
        for entry in self.cur.fetchall():
            if entry[2] != 'TEXT' and entry[1] != 'college_id':
                self.data_types.append(entry[1])
        self.max_college_data_index = len(self.data_types) - 1
        self.cur.execute('''
            PRAGMA table_info("%s")''' % self.year_names[0])
        for entry in self.cur.fetchall()[1:]: #ignores duplicate 'college_id'
            if entry[2] != 'TEXT':
                self.data_types.append(entry[1])

    def _get_year_names(self):
        """Retrieve the valid years from the database and store them."""
        self.cur.execute('''
            SELECT name FROM sqlite_master WHERE type = "table"''')
        for item in self.cur.fetchall():
            if item[0] != 'College' and item[0] != 'sqlite_sequence':
                self.year_names.append(item[0])

class PlotConfigWindow(QtGui.QWidget):
    """Menu for user specification of data to be plotted.

    The user selects the data to be plotted from drop down boxes on the
    PlotConfigWindow (see SeriesOptions class).

    Attributes:
        parent: MainWindow parent object.
        layout: Layout for structuring the window's widgets.
        series_options: List of SeriesOptions objects.
        add_btn: Button to add a new SeriesOption widget to the window.
        confirm_btn: Button that calls for the SeriesOptions to be plotted.
    """

    def __init__(self, parent, college_names, year_names, data_types):
        QtGui.QWidget.__init__(self)
        self.parent = parent

        self.layout = QtGui.QVBoxLayout(self)

        self.series_options = []

        self.add_btn = QtGui.QPushButton('Add Data Series')
        QtCore.QObject.connect(
            self.add_btn, QtCore.SIGNAL('clicked()'),
            lambda: self._addSeries(college_names, year_names, data_types))
        self.layout.addWidget(self.add_btn)

        self.confirm_button = QtGui.QPushButton('Plot Series')
        QtCore.QObject.connect(
            self.confirm_button, QtCore.SIGNAL('clicked()'),
            self.get_plot_settings)
        self.layout.addWidget(self.confirm_button)

    def _addSeries(self, college_names, year_names, data_types):
        """Adds a new SeriesOption to the window."""
        options = SeriesOptions(self, college_names, year_names, data_types)
        self.series_options.insert(0, options)
        self.layout.insertWidget(0, options)

    def get_plot_settings(self):
        """Send information to be stored in PlotSettings object."""
        if len(self.series_options) > 20:
            print('Maximum number of plots supported is 20.')
            self.close()
            return
        self.parent.plot_settings.clear_series_plots()
        for option in self.series_options:
            self.parent.plot_settings.add_series_plot(option.get_series())
        self.parent.plot_settings.query_db()
        self.parent.main.update_figure()
        self.close()

class SeriesOptions(QtGui.QWidget):
    """Widget containing boxes for users to select data to be plotted.

    Attributes:
        layout: Layout of each row of boxes - arranged horizontally.
        parent: PlotConfigWindow object containing this SeriesOptions.
        schoolbox: Drop down box to select the college.
        databox: Drop down box to select the data type.
        startyearbox: Drop down box to select the beginning year for the data.
        endyearbox: Drop down box to select the end year for the data.
        removebox: Button to delete this from the PlotConfigWindow.
    """

    def __init__(self, parent, college_names, year_names, data_types):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QHBoxLayout(self)
        self.parent = parent

        self.schoolbox = QtGui.QComboBox()
        for college in college_names:
            self.schoolbox.addItem(college)
        self.layout.addWidget(self.schoolbox)

        self.databox = QtGui.QComboBox()
        for data_type in data_types:
            self.databox.addItem(data_type)
        self.layout.addWidget(self.databox)

        self.startyearbox = QtGui.QComboBox()
        for year in year_names:
            self.startyearbox.addItem(year)
        self.layout.addWidget(self.startyearbox)

        self.endyearbox = QtGui.QComboBox()
        for year in year_names:
            self.endyearbox.addItem(year)
        self.layout.addWidget(self.endyearbox)

        self.removebox = QtGui.QPushButton('Remove Series')
        QtCore.QObject.connect(
            self.removebox, QtCore.SIGNAL('clicked()'), self.remove_plot)
        self.layout.addWidget(self.removebox)

    def get_series(self):
        """Create a SeriesPlot object from selected data.

        Returns:
            series_plot: SeriesPlot object created from user-selected data.
        """
        is_college_data = (self.databox.currentIndex() <=
            self.parent.parent.plot_settings.max_college_data_index)
        series_plot = SeriesPlot(
            str(self.schoolbox.currentText()),
            str(self.databox.currentText()),
            str(self.startyearbox.currentText()),
            str(self.endyearbox.currentText()),
            is_college_data)
        return series_plot

    def remove_plot(self):
        """Remove this SeriesOptions from the PlotConfigWindow."""
        self.parent.series_options.remove(self)
        self.deleteLater()

class SeriesPlot():
    """Stores the information about a single series to be plotted.

    Attributes:
        college: College name string.
        data_type: Data type string.
        start_year: Starting year string.
        end_year: Ending year string.
        data: List of data from the database for college's data_type between
            start_year and end_year, inclusive.
    """

    def __init__(self, college, data_type, start_year, end_year, is_college):
        self.college = college
        self.data_type = data_type
        self.start_year = start_year
        self.end_year = end_year
        self.is_college = is_college
        self.data = []

    def get_xy_data(self):
        """Generates a list of x and y coordinates to be plotted.

        Returns:
            (x_data, y_data): tuple containing list of x values and list of y
                values
        """
        x_data = list(
            range(int(self.start_year), int(self.end_year) + 1))
        y_data = []
        if self.is_college:
            y_data = [self.data[0] for val in x_data]
        else:
            y_data = self.data
        return (x_data, y_data)

    def to_string(self):
        """Convenience method to convert SeriesPlot to a string."""
        return self.college, self.data_type, self.start_year, self.end_year
