from setuptools import setup, find_packages

setup(
    name="slack_msg_clean",
    version="0.1.0",
    author="Jihun Yoon",
    author_email="yjh4374@gmail.com",
    description="A Slack bot to delete your messages in any channel or DM",
    url="https://github.com/jihun-yoon/slack_msg_clean",
    packages=find_packages(),
    install_requires=["slack-bolt>=1.0.0", "slack-sdk>=3.0.0"],
    entry_points={"console_scripts": ["slack-msg-clean=slack_msg_clean.app:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
