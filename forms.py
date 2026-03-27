from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")


class ArtworkForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10)])
    hashtags = StringField("Hashtags (comma separated)", validators=[Length(max=500)])
    status = SelectField(
        "Status",
        choices=[("available", "Available"), ("reserved", "Reserved"), ("sold", "Sold")],
    )
    image_url = StringField("Image URL", validators=[DataRequired()])
    submit = SubmitField("Upload Artwork")


class ArtworkEditForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10)])
    hashtags = StringField("Hashtags (comma separated)", validators=[Length(max=500)])
    status = SelectField(
        "Status",
        choices=[("available", "Available"), ("reserved", "Reserved"), ("sold", "Sold")],
    )
    image_url = StringField("Image URL (optional)")
    submit = SubmitField("Save Changes")


class PurchaseRequestForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=160)])
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(max=40)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=160)])
    message = TextAreaField("Message (optional)", validators=[Length(max=1000)])
    submit = SubmitField("Submit Request")


class RequestStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[("new", "New"), ("contacted", "Contacted"), ("closed", "Closed")],
    )
    submit = SubmitField("Update")


class DeleteForm(FlaskForm):
    submit = SubmitField("Delete")
