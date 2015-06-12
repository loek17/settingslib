Get Started
===========

Quick start
-----------

.. code-block:: python
    
    from settingslib.basesettings import BaseSettings
    
    class Settings(BaseSettings):
        PORT = 4352
        USER = 'user'
        PASSWORD = 'admin'

    settings = Settings()
    
    # store the settings some where to always have access to it

Simply extend the BaseSettings class and add UPPER CASE attrs. After
that create the settingsobject.

In order to set settings at runtime you need to set a user config file
on the settingsobject using ``settings.set_userfile(file)``.

Example:

.. code-block:: python
    
    settings.set_userfile(file)
    
    settings.USER = 'Some Someone'
    settings.save()
    
    # next time the app is started the value USER will be 'Some Someone' instate of 'user' 

Getting a settings value
------------------------

Settingsvalues are found in the following order:

- First: The commandline option are check if key attr key exist.
- Second: The userconfigfile is check if the key was set a runtime or in a previous runtime
- Third: The nosave dict is check if the value was set at this runtime
- Fourth: The enviroment is check if it contains the attr key prefixed with the passed prefix
- Fifth: All the configfile are check in the order that where are added. 
- Sixth: The default is returned.